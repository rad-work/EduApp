"""add problem difficulty

Revision ID: 7e8f9a0b1c2d
Revises: 2f4a1b9f5c11
Create Date: 2026-05-19 12:00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "7e8f9a0b1c2d"
down_revision: Union[str, Sequence[str], None] = "2f4a1b9f5c11"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

problem_difficulty_enum = postgresql.ENUM(
    "easy",
    "medium",
    "hard",
    name="problem_difficulty_enum",
    create_type=False,
)


def upgrade() -> None:
    problem_difficulty_enum.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "problems",
        sa.Column(
            "difficulty",
            problem_difficulty_enum,
            nullable=False,
            server_default="medium",
        ),
    )
    op.alter_column("problems", "difficulty", server_default=None)


def downgrade() -> None:
    op.drop_column("problems", "difficulty")
    problem_difficulty_enum.drop(op.get_bind(), checkfirst=True)
