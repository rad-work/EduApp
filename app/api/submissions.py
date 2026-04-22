from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models import Problem, Submission, SubmissionStatus, User
from app.services.queue import enqueue_submission
from app.schemas import SubmissionStatusResponse

router = APIRouter(prefix="/api/submissions", tags=["submissions"])


@router.post("", response_model=SubmissionStatusResponse, status_code=status.HTTP_201_CREATED)
def create_submission(
    problem_id: int,
    language: str,
    source_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Submission:
    problem_exists = db.scalar(select(Problem.id).where(Problem.id == problem_id))
    if not problem_exists:
        raise HTTPException(status_code=404, detail="Problem not found")

    submission = Submission(
        user_id=current_user.id,
        problem_id=problem_id,
        language=language.strip(),
        source_code=source_code,
        status=SubmissionStatus.QUEUED,
        queued_at=datetime.now(UTC),
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    enqueue_submission(submission.id)
    return submission


@router.get("/{submission_id}/status", response_model=SubmissionStatusResponse)
def get_submission_status(
    submission_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Submission:
    submission = db.scalar(select(Submission).where(Submission.id == submission_id))
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found")
    is_admin = current_user.role.value == "admin"
    if submission.user_id != current_user.id and not is_admin:
        raise HTTPException(status_code=403, detail="Forbidden")
    return submission
