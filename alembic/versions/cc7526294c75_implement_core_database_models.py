"""implement core database models

Revision ID: cc7526294c75
Revises: 
Create Date: 2026-04-22 09:34:04.498755
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'cc7526294c75'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    user_role_enum = postgresql.ENUM("ADMIN", "USER", name="user_role_enum", create_type=False)
    submission_status_enum = postgresql.ENUM(
        "PENDING",
        "QUEUED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        name="submission_status_enum",
        create_type=False,
    )
    verdict_enum = postgresql.ENUM(
        "ACCEPTED",
        "WRONG_ANSWER",
        "TIME_LIMIT_EXCEEDED",
        "MEMORY_LIMIT_EXCEEDED",
        "RUNTIME_ERROR",
        "COMPILATION_ERROR",
        "PRESENTATION_ERROR",
        "SYSTEM_ERROR",
        name="verdict_enum",
        create_type=False,
    )

    user_role_enum.create(op.get_bind(), checkfirst=True)
    submission_status_enum.create(op.get_bind(), checkfirst=True)
    verdict_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_tags_name"), "tags", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(length=64), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", user_role_enum, nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_username"), "users", ["username"], unique=True)

    op.create_table(
        "problems",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("statement", sa.Text(), nullable=False),
        sa.Column("author_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["author_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_problems_author_id"), "problems", ["author_id"], unique=False)
    op.create_index(op.f("ix_problems_slug"), "problems", ["slug"], unique=True)

    op.create_table(
        "problem_tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("problem_id", "tag_id", name="uq_problem_tag"),
    )
    op.create_index(op.f("ix_problem_tags_problem_id"), "problem_tags", ["problem_id"], unique=False)
    op.create_index(op.f("ix_problem_tags_tag_id"), "problem_tags", ["tag_id"], unique=False)

    op.create_table(
        "submissions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("source_code", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("status", submission_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_submissions_problem_id"), "submissions", ["problem_id"], unique=False)
    op.create_index(op.f("ix_submissions_user_id"), "submissions", ["user_id"], unique=False)
    op.create_index("ix_submissions_user_problem", "submissions", ["user_id", "problem_id"], unique=False)

    op.create_table(
        "test_cases",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("problem_id", sa.Integer(), nullable=False),
        sa.Column("input_data", sa.Text(), nullable=False),
        sa.Column("expected_output", sa.Text(), nullable=False),
        sa.Column("is_sample", sa.Boolean(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["problem_id"], ["problems.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_test_cases_problem_id"), "test_cases", ["problem_id"], unique=False)
    op.create_index("ix_test_cases_problem_order", "test_cases", ["problem_id", "order_index"], unique=False)

    op.create_table(
        "submission_results",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("test_case_id", sa.Integer(), nullable=True),
        sa.Column("verdict", verdict_enum, nullable=False),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("memory_kb", sa.Integer(), nullable=True),
        sa.Column("message", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["submission_id"], ["submissions.id"]),
        sa.ForeignKeyConstraint(["test_case_id"], ["test_cases.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("submission_id", "test_case_id", name="uq_submission_result_case"),
    )
    op.create_index(op.f("ix_submission_results_submission_id"), "submission_results", ["submission_id"], unique=False)
    op.create_index(op.f("ix_submission_results_test_case_id"), "submission_results", ["test_case_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_submission_results_test_case_id"), table_name="submission_results")
    op.drop_index(op.f("ix_submission_results_submission_id"), table_name="submission_results")
    op.drop_table("submission_results")

    op.drop_index("ix_test_cases_problem_order", table_name="test_cases")
    op.drop_index(op.f("ix_test_cases_problem_id"), table_name="test_cases")
    op.drop_table("test_cases")

    op.drop_index("ix_submissions_user_problem", table_name="submissions")
    op.drop_index(op.f("ix_submissions_user_id"), table_name="submissions")
    op.drop_index(op.f("ix_submissions_problem_id"), table_name="submissions")
    op.drop_table("submissions")

    op.drop_index(op.f("ix_problem_tags_tag_id"), table_name="problem_tags")
    op.drop_index(op.f("ix_problem_tags_problem_id"), table_name="problem_tags")
    op.drop_table("problem_tags")

    op.drop_index(op.f("ix_problems_slug"), table_name="problems")
    op.drop_index(op.f("ix_problems_author_id"), table_name="problems")
    op.drop_table("problems")

    op.drop_index(op.f("ix_users_username"), table_name="users")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    op.drop_index(op.f("ix_tags_name"), table_name="tags")
    op.drop_table("tags")

    sa.Enum(name="verdict_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="submission_status_enum").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role_enum").drop(op.get_bind(), checkfirst=True)
