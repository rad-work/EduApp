from dataclasses import dataclass
from math import ceil
from typing import TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

T = TypeVar("T")

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100


@dataclass(frozen=True)
class Page:
    items: list
    page: int
    page_size: int
    total: int
    total_pages: int

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages

    @property
    def prev_page(self) -> int:
        return max(1, self.page - 1)

    @property
    def next_page(self) -> int:
        return min(self.total_pages, self.page + 1)


def normalize_page(page: int) -> int:
    return max(1, page)


def normalize_page_size(page_size: int) -> int:
    if page_size < 1:
        return DEFAULT_PAGE_SIZE
    return min(page_size, MAX_PAGE_SIZE)


def paginate(db: Session, stmt: Select[tuple[T]], page: int, page_size: int) -> Page:
    page = normalize_page(page)
    page_size = normalize_page_size(page_size)
    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    total_pages = max(1, ceil(total / page_size)) if total else 1
    if page > total_pages:
        page = total_pages
    offset = (page - 1) * page_size
    items = list(db.scalars(stmt.limit(page_size).offset(offset)).all())
    return Page(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
        total_pages=total_pages,
    )
