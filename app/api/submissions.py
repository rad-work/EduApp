from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Problem, Submission, SubmissionResult, SubmissionStatus, User
from app.services.queue import enqueue_submission
from app.schemas import SubmissionCreateRequest, SubmissionStatusResponse

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionStatusResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    payload: SubmissionCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmissionStatusResponse:
    problem_exists = db.scalar(select(Problem.id).where(Problem.id == payload.problem_id))
    if not problem_exists:
        raise HTTPException(status_code=404, detail="Problem not found")

    submission = Submission(
        user_id=current_user.id,
        problem_id=payload.problem_id,
        language=payload.language.strip(),
        source_code=payload.source_code,
        status=SubmissionStatus.QUEUED,
        queued_at=datetime.now(UTC),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    enqueue_submission(submission.id)
    return SubmissionStatusResponse(
        id=submission.id,
        status=submission.status.value,
        language=submission.language,
        problem_id=submission.problem_id,
        created_at=submission.created_at,
        queued_at=submission.queued_at,
        finished_at=submission.finished_at,
        verdict=None,
        message=None,
        is_final=False,
    )


@router.get("/{submission_id}/status", response_model=SubmissionStatusResponse)
def get_submission_status(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SubmissionStatusResponse:
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
    is_final = submission.status in (SubmissionStatus.COMPLETED, SubmissionStatus.FAILED)
    return SubmissionStatusResponse(
        id=submission.id,
        status=submission.status.value,
        language=submission.language,
        problem_id=submission.problem_id,
        created_at=submission.created_at,
        queued_at=submission.queued_at,
        finished_at=submission.finished_at,
        verdict=latest_result.verdict.value if latest_result else None,
        message=latest_result.message if latest_result else None,
        is_final=is_final,
    )
