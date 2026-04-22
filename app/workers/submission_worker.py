from datetime import UTC, datetime

from sqlalchemy import select

from app.core.database import SessionLocal
from app.models import Submission, SubmissionResult, SubmissionStatus, Verdict


def process_submission_job(submission_id: int) -> None:
    db = SessionLocal()
    try:
        submission = db.get(Submission, submission_id)
        if not submission:
            return

        submission.status = SubmissionStatus.RUNNING
        db.commit()

        # Stub execution pipeline: always return runtime error for now.
        submission.status = SubmissionStatus.COMPLETED
        submission.finished_at = datetime.now(UTC)

        existing_result = db.scalar(
            select(SubmissionResult).where(
                SubmissionResult.submission_id == submission_id,
                SubmissionResult.test_case_id.is_(None),
            )
        )
        if not existing_result:
            db.add(
                SubmissionResult(
                    submission_id=submission_id,
                    test_case_id=None,
                    verdict=Verdict.RUNTIME_ERROR,
                    message="Stub worker verdict: runtime error",
                )
            )
        db.commit()
    except Exception:
        submission = db.get(Submission, submission_id)
        if submission:
            submission.status = SubmissionStatus.FAILED
            submission.finished_at = datetime.now(UTC)
            db.commit()
        raise
    finally:
        db.close()
