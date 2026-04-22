from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_role
from app.core.config import settings
from app.core.database import get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models import User, UserRole

router = APIRouter(tags=["pages"])
templates = Jinja2Templates(directory="templates")


@router.get("/", response_class=HTMLResponse)
def index(request: Request, current_user: User = Depends(get_current_user)) -> HTMLResponse:
    return templates.TemplateResponse(
        request,
        "index.html",
        {"user": current_user},
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
