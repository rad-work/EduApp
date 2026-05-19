from dataclasses import dataclass

from sqlalchemy import distinct, func, select
from sqlalchemy.orm import Session

from app.models import ProblemTag, Submission, SubmissionResult, Tag, Verdict


@dataclass(frozen=True)
class ProblemStats:
    attempt_count: int
    ac_count: int


@dataclass(frozen=True)
class UserStats:
    attempt_count: int
    solved_count: int


@dataclass(frozen=True)
class UserProblemStats:
    attempt_count: int
    solved: bool


def get_problem_stats(db: Session, problem_ids: list[int]) -> dict[int, ProblemStats]:
    if not problem_ids:
        return {}

    attempts_rows = db.execute(
        select(Submission.problem_id, func.count(Submission.id))
        .where(Submission.problem_id.in_(problem_ids))
        .group_by(Submission.problem_id)
    ).all()
    attempts = {problem_id: count for problem_id, count in attempts_rows}

    ac_rows = db.execute(
        select(Submission.problem_id, func.count(distinct(Submission.user_id)))
        .join(SubmissionResult, SubmissionResult.submission_id == Submission.id)
        .where(
            Submission.problem_id.in_(problem_ids),
            SubmissionResult.verdict == Verdict.ACCEPTED,
        )
        .group_by(Submission.problem_id)
    ).all()
    ac_counts = {problem_id: count for problem_id, count in ac_rows}

    return {
        problem_id: ProblemStats(
            attempt_count=attempts.get(problem_id, 0),
            ac_count=ac_counts.get(problem_id, 0),
        )
        for problem_id in problem_ids
    }


def get_user_stats(db: Session, user_id: int) -> UserStats:
    attempt_count = db.scalar(
        select(func.count(Submission.id)).where(Submission.user_id == user_id)
    ) or 0
    solved_count = db.scalar(
        select(func.count(distinct(Submission.problem_id)))
        .join(SubmissionResult, SubmissionResult.submission_id == Submission.id)
        .where(
            Submission.user_id == user_id,
            SubmissionResult.verdict == Verdict.ACCEPTED,
        )
    ) or 0
    return UserStats(attempt_count=attempt_count, solved_count=solved_count)


def get_user_problem_stats(db: Session, user_id: int, problem_id: int) -> UserProblemStats:
    attempt_count = db.scalar(
        select(func.count(Submission.id)).where(
            Submission.user_id == user_id,
            Submission.problem_id == problem_id,
        )
    ) or 0
    has_ac = db.scalar(
        select(func.count(Submission.id))
        .join(SubmissionResult, SubmissionResult.submission_id == Submission.id)
        .where(
            Submission.user_id == user_id,
            Submission.problem_id == problem_id,
            SubmissionResult.verdict == Verdict.ACCEPTED,
        )
    )
    return UserProblemStats(attempt_count=attempt_count, solved=bool(has_ac))


def get_all_tag_names(db: Session) -> list[str]:
    return list(db.scalars(select(Tag.name).order_by(Tag.name.asc())).all())


def sync_problem_tags(db: Session, problem_id: int, tag_names: list[str]) -> None:
    normalized = sorted({name.strip().lower() for name in tag_names if name.strip()})
    existing_links = db.scalars(
        select(ProblemTag).where(ProblemTag.problem_id == problem_id)
    ).all()
    for link in existing_links:
        db.delete(link)
    db.flush()

    if not normalized:
        return

    tags_by_name: dict[str, Tag] = {}
    for name in normalized:
        tag = db.scalar(select(Tag).where(Tag.name == name))
        if not tag:
            tag = Tag(name=name)
            db.add(tag)
            db.flush()
        tags_by_name[name] = tag

    for name in normalized:
        db.add(ProblemTag(problem_id=problem_id, tag_id=tags_by_name[name].id))


def problem_tag_names(problem) -> list[str]:
    return sorted(link.tag.name for link in problem.tags)


def get_latest_verdicts(db: Session, submission_ids: list[int]) -> dict[int, Verdict | None]:
    if not submission_ids:
        return {}
    latest_ids = (
        select(
            SubmissionResult.submission_id,
            func.max(SubmissionResult.id).label("max_id"),
        )
        .where(SubmissionResult.submission_id.in_(submission_ids))
        .group_by(SubmissionResult.submission_id)
        .subquery()
    )
    rows = db.execute(
        select(SubmissionResult.submission_id, SubmissionResult.verdict).join(
            latest_ids,
            SubmissionResult.id == latest_ids.c.max_id,
        )
    ).all()
    return {submission_id: verdict for submission_id, verdict in rows}
