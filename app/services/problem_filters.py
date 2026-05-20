from sqlalchemy import Select, select
from sqlalchemy.orm import selectinload

from app.models import Problem, ProblemDifficulty, ProblemTag, Tag


def parse_tag_filter(tags: str | None = None, selected: list[str] | None = None) -> list[str]:
    names: list[str] = []
    if selected:
        names.extend(part.strip().lower() for part in selected if part and part.strip())
    if tags:
        names.extend(part.strip().lower() for part in tags.split(",") if part.strip())
    return sorted(set(names))


def build_problem_list_query(
    *,
    include_archived: bool = False,
    difficulty: ProblemDifficulty | None = None,
    tag_names: list[str] | None = None,
) -> Select[tuple[Problem]]:
    stmt = (
        select(Problem)
        .options(
            selectinload(Problem.tags).selectinload(ProblemTag.tag),
        )
        .order_by(Problem.id.desc())
    )
    if not include_archived:
        stmt = stmt.where(Problem.is_archived.is_(False))
    if difficulty is not None:
        stmt = stmt.where(Problem.difficulty == difficulty)
    if tag_names:
        for tag_name in tag_names:
            stmt = stmt.where(
                Problem.id.in_(
                    select(ProblemTag.problem_id)
                    .join(Tag, Tag.id == ProblemTag.tag_id)
                    .where(Tag.name == tag_name)
                )
            )
    return stmt
