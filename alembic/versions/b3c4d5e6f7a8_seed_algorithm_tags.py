"""seed algorithm tags

Revision ID: b3c4d5e6f7a8
Revises: 7e8f9a0b1c2d
Create Date: 2026-05-19 18:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, Sequence[str], None] = "7e8f9a0b1c2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Базовые теги для олимпиадных / алгоритмических задач
ALGORITHM_TAGS: tuple[str, ...] = (
    "implementation",
    "math",
    "greedy",
    "dp",
    "data_structures",
    "graphs",
    "trees",
    "strings",
    "geometry",
    "binary_search",
    "two_pointers",
    "sorting",
    "combinatorics",
    "number_theory",
    "dfs_and_bfs",
    "shortest_paths",
    "divide_and_conquer",
    "bitmasks",
    "constructive",
    "simulation",
    "games",
    "flows",
    "dsu",
    "hashing",
    "interactive",
)


def upgrade() -> None:
    conn = op.get_bind()
    for name in ALGORITHM_TAGS:
        conn.execute(
            sa.text("INSERT INTO tags (name) VALUES (:name) ON CONFLICT (name) DO NOTHING"),
            {"name": name},
        )


def downgrade() -> None:
    conn = op.get_bind()
    for name in ALGORITHM_TAGS:
        conn.execute(
            sa.text(
                """
                DELETE FROM problem_tags
                WHERE tag_id IN (SELECT id FROM tags WHERE name = :name)
                """
            ),
            {"name": name},
        )
        conn.execute(
            sa.text("DELETE FROM tags WHERE name = :name"),
            {"name": name},
        )
