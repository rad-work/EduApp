"""add problem archive flag

Revision ID: 2f4a1b9f5c11
Revises: cc7526294c75
Create Date: 2026-04-22 13:30:00
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "2f4a1b9f5c11"
down_revision: Union[str, Sequence[str], None] = "cc7526294c75"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "problems",
        sa.Column("is_archived", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("problems", "is_archived", server_default=None)


def downgrade() -> None:
    op.drop_column("problems", "is_archived")
