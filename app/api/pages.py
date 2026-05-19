from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.api.deps import get_current_user, get_optional_user, require_role
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import (
    Problem,
    ProblemDifficulty,
    ProblemTag,
    Submission,
    SubmissionResult,
    SubmissionStatus,
    TestCase,
    User,
    UserRole,
)
from app.services.pagination import paginate
from app.services.problem_filters import build_problem_list_query, parse_tag_filter
from app.services.query_string import build_query_string
from app.services.queue import enqueue_submission
from app.services.stats import (
    ProblemStats,
    get_all_tag_names,
    get_latest_verdicts,
    get_problem_stats,
    get_user_problem_stats,
    get_user_stats,
    problem_tag_names,
    sync_problem_tags,
)

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request) -> RedirectResponse:
    return RedirectResponse("/problems", status_code=302)


@router.get("/problems", response_class=HTMLResponse)
def problem_list(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
    difficulty: str | None = Query(None),
    tags: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> HTMLResponse:
    difficulty_filter: ProblemDifficulty | None = None
    if difficulty:
        try:
            difficulty_filter = ProblemDifficulty(difficulty)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid difficulty") from exc

    tag_names = parse_tag_filter(tags)
    stmt = build_problem_list_query(difficulty=difficulty_filter, tag_names=tag_names or None)
    problem_page = paginate(db, stmt, page, page_size)
    problem_ids = [problem.id for problem in problem_page.items]
    stats_by_problem = get_problem_stats(db, problem_ids)
    user_stats = get_user_stats(db, current_user.id) if current_user else None
    all_tags = get_all_tag_names(db)
    query_string = build_query_string(difficulty=difficulty, tags=tags, page_size=page_size)

    return templates.TemplateResponse(
        request,
        "problem_list.html",
        {
            "user": current_user,
            "page": problem_page,
            "stats_by_problem": stats_by_problem,
            "user_stats": user_stats,
            "all_tags": all_tags,
            "difficulty": difficulty,
            "tags": tags,
            "query_string": query_string,
            "problem_tag_names": problem_tag_names,
            "difficulties": list(ProblemDifficulty),
        },
    )


@router.get("/problems/{slug}", response_class=HTMLResponse)
def problem_detail(
    slug: str,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
) -> HTMLResponse:
    problem = db.scalar(
        select(Problem)
        .options(selectinload(Problem.tags).selectinload(ProblemTag.tag))
        .where(
            Problem.slug == slug,
            Problem.is_archived.is_(False),
        )
    )
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    samples = db.scalars(
        select(TestCase)
        .where(TestCase.problem_id == problem.id, TestCase.is_sample.is_(True))
        .order_by(TestCase.order_index.asc(), TestCase.id.asc())
    ).all()
    problem_stats = get_problem_stats(db, [problem.id]).get(problem.id, ProblemStats(0, 0))
    user_problem_stats = (
        get_user_problem_stats(db, current_user.id, problem.id) if current_user else None
    )
    return templates.TemplateResponse(
        request,
        "problem_detail.html",
        {
            "user": current_user,
            "problem": problem,
            "samples": samples,
            "problem_stats": problem_stats,
            "user_problem_stats": user_problem_stats,
            "problem_tag_names": problem_tag_names,
        },
    )


@router.post("/problems/{slug}/submit")
def submit_solution(
    slug: str,
    language: str = Form(...),
    source_code: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> RedirectResponse:
    problem = db.scalar(
        select(Problem).where(
            Problem.slug == slug,
            Problem.is_archived.is_(False),
        )
    )
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")

    submission = Submission(
        user_id=current_user.id,
        problem_id=problem.id,
        language=language.strip(),
        source_code=source_code,
        status=SubmissionStatus.QUEUED,
        queued_at=datetime.now(UTC),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    enqueue_submission(submission.id)
    return RedirectResponse(f"/submissions/{submission.id}", status_code=303)


@router.get("/submissions", response_class=HTMLResponse)
def my_submissions(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
) -> HTMLResponse:
    stmt = (
        select(Submission)
        .where(Submission.user_id == current_user.id)
        .options(selectinload(Submission.problem))
        .order_by(Submission.id.desc())
    )
    submission_page = paginate(db, stmt, page, page_size)
    submission_ids = [submission.id for submission in submission_page.items]
    verdicts = get_latest_verdicts(db, submission_ids)
    user_stats = get_user_stats(db, current_user.id)
    query_string = build_query_string(page_size=page_size)

    return templates.TemplateResponse(
        request,
        "submission_list.html",
        {
            "user": current_user,
            "page": submission_page,
            "verdicts": verdicts,
            "user_stats": user_stats,
            "query_string": query_string,
        },
    )


@router.get("/submissions/{submission_id}", response_class=HTMLResponse)
def submission_detail(
    submission_id: int,
    request: Request,
    poll: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> HTMLResponse:
    submission = db.scalar(select(Submission).where(Submission.id == submission_id))
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    is_admin = current_user.role.value == "admin"
    if submission.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    latest_result = db.scalar(
        select(SubmissionResult)
        .where(SubmissionResult.submission_id == submission.id)
        .order_by(SubmissionResult.id.desc())
    )
    if poll:
        is_final = submission.status in (SubmissionStatus.COMPLETED, SubmissionStatus.FAILED)
        return JSONResponse(
            {
                "id": submission.id,
                "status": submission.status.value,
                "verdict": latest_result.verdict.value if latest_result else None,
                "message": latest_result.message if latest_result else None,
                "is_final": is_final,
                "finished_at": submission.finished_at.isoformat() if submission.finished_at else None,
            }
        )
    return templates.TemplateResponse(
        request,
        "submission_detail.html",
        {"user": current_user, "submission": submission, "latest_result": latest_result},
    )


@router.get("/admin", response_class=HTMLResponse)
def admin_page(
    request: Request,
    current_user: User = Depends(require_role("admin")),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "admin.html",
        {"user": current_user},
    )


@router.get("/admin/problems", response_class=HTMLResponse)
def admin_problems(
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> HTMLResponse:
    problems = db.scalars(select(Problem).order_by(Problem.id.desc())).all()
    return templates.TemplateResponse(
        request,
        "admin_problem_list.html",
        {"user": current_user, "problems": problems},
    )


@router.get("/admin/problems/new", response_class=HTMLResponse)
def admin_problem_new_page(
    request: Request,
    current_user: User = Depends(require_role("admin")),
) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "admin_problem_form.html",
        {
            "user": current_user,
            "problem": None,
            "error": None,
            "tag_list": [],
            "difficulties": list(ProblemDifficulty),
        },
    )


@router.post("/admin/problems/new")
def admin_problem_create(
    request: Request,
    title: str = Form(...),
    slug: str = Form(...),
    statement: str = Form(...),
    difficulty: str = Form(ProblemDifficulty.MEDIUM.value),
    tags: str = Form(""),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> HTMLResponse:
    existing = db.scalar(select(Problem).where(Problem.slug == slug))
    if existing:
        return templates.TemplateResponse(
            request,
            "admin_problem_form.html",
            {"user": current_user, "problem": None, "error": "Slug уже занят"},
            status_code=409,
        )
    try:
        problem_difficulty = ProblemDifficulty(difficulty)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid difficulty") from exc

    problem = Problem(
        title=title.strip(),
        slug=slug.strip(),
        statement=statement.strip(),
        author_id=current_user.id,
        difficulty=problem_difficulty,
        is_archived=False,
    )
    db.add(problem)
    db.commit()
    db.refresh(problem)
    sync_problem_tags(db, problem.id, tags.split(","))
    db.commit()
    return RedirectResponse("/admin/problems", status_code=303)


@router.get("/admin/problems/{problem_id}/edit", response_class=HTMLResponse)
def admin_problem_edit_page(
    problem_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
) -> HTMLResponse:
    problem = db.scalar(
        select(Problem)
        .options(selectinload(Problem.tags).selectinload(ProblemTag.tag))
        .where(Problem.id == problem_id)
    )
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    tests = db.scalars(
        select(TestCase).where(TestCase.problem_id == problem_id).order_by(TestCase.order_index.asc())
    ).all()
    tag_list = problem_tag_names(problem)
    return templates.TemplateResponse(
        request,
        "admin_problem_form.html",
        {
            "user": current_user,
            "problem": problem,
            "tests": tests,
            "error": None,
            "tag_list": tag_list,
            "difficulties": list(ProblemDifficulty),
        },
    )


@router.post("/admin/problems/{problem_id}/edit")
def admin_problem_edit(
    problem_id: int,
    title: str = Form(...),
    slug: str = Form(...),
    statement: str = Form(...),
    difficulty: str = Form(...),
    tags: str = Form(""),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> RedirectResponse:
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    duplicate = db.scalar(select(Problem).where(Problem.slug == slug.strip(), Problem.id != problem_id))
    if duplicate:
        raise HTTPException(status_code=409, detail="Slug already exists")
    try:
        problem.difficulty = ProblemDifficulty(difficulty)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Invalid difficulty") from exc
    problem.title = title.strip()
    problem.slug = slug.strip()
    problem.statement = statement.strip()
    sync_problem_tags(db, problem_id, tags.split(","))
    db.commit()
    return RedirectResponse(f"/admin/problems/{problem_id}/edit", status_code=303)


@router.post("/admin/problems/{problem_id}/archive")
def admin_problem_archive(
    problem_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> RedirectResponse:
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    problem.is_archived = not problem.is_archived
    db.commit()
    return RedirectResponse("/admin/problems", status_code=303)


@router.post("/admin/problems/{problem_id}/tests")
def admin_problem_add_test(
    problem_id: int,
    input_data: str = Form(...),
    expected_output: str = Form(...),
    order_index: int = Form(0),
    is_sample: bool = Form(False),
    db: Session = Depends(get_db),
    _: User = Depends(require_role("admin")),
) -> RedirectResponse:
    problem = db.get(Problem, problem_id)
    if not problem:
        raise HTTPException(status_code=404, detail="Problem not found")
    test_case = TestCase(
        problem_id=problem_id,
        input_data=input_data,
        expected_output=expected_output,
        order_index=order_index,
        is_sample=is_sample,
    )
    db.add(test_case)
    db.commit()
    return RedirectResponse(f"/admin/problems/{problem_id}/edit", status_code=303)


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login", response_class=HTMLResponse)
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    user = db.scalar(select(User).where(User.username == username))
    if not user or not verify_password(password, user.password_hash):
        return templates.TemplateResponse(
            request,
            "login.html",
            {"error": "Неверный логин или пароль"},
            status_code=401,
        )

    token = create_access_token(str(user.id))
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        path="/",
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.access_token_expire_minutes * 60,
    )
    return response


@router.get("/register", response_class=HTMLResponse)
def register_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "register.html", {"error": None})


@router.post("/register", response_class=HTMLResponse)
def register_submit(
    request: Request,
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    existing = db.scalar(select(User).where(or_(User.username == username, User.email == email)))
    if existing:
        return templates.TemplateResponse(
            request,
            "register.html",
            {"error": "Пользователь с таким username/email уже существует"},
            status_code=409,
        )

    user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password),
        role=UserRole.USER,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token(str(user.id))
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=token,
        path="/",
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=settings.access_token_expire_minutes * 60,
    )
    return response


@router.post("/logout")
def logout_submit() -> RedirectResponse:
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(key=settings.auth_cookie_name, path="/")
    return response


@router.get("/logout")
def logout_page() -> RedirectResponse:
    response = RedirectResponse("/login", status_code=303)
    response.delete_cookie(key=settings.auth_cookie_name, path="/")
    return response
