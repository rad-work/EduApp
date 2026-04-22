from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.enums import SubmissionStatus, UserRole, Verdict


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        nullable=False,
        default=UserRole.USER,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )

    created_problems = relationship("Problem", back_populates="author")
    submissions = relationship("Submission", back_populates="user")


class Problem(Base):
    __tablename__ = "problems"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )

    author = relationship("User", back_populates="created_problems")
    test_cases = relationship("TestCase", back_populates="problem", cascade="all, delete-orphan")
    submissions = relationship("Submission", back_populates="problem")
    tags = relationship("ProblemTag", back_populates="problem", cascade="all, delete-orphan")


class TestCase(Base):
    __tablename__ = "test_cases"
    __table_args__ = (
        Index("ix_test_cases_problem_order", "problem_id", "order_index"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=False, index=True)
    input_data: Mapped[str] = mapped_column(Text, nullable=False)
    expected_output: Mapped[str] = mapped_column(Text, nullable=False)
    is_sample: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    problem = relationship("Problem", back_populates="test_cases")
    results = relationship("SubmissionResult", back_populates="test_case")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_user_problem", "user_id", "problem_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=False, index=True)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    status: Mapped[SubmissionStatus] = mapped_column(
        Enum(SubmissionStatus, name="submission_status_enum"),
        nullable=False,
        default=SubmissionStatus.PENDING,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    queued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="submissions")
    problem = relationship("Problem", back_populates="submissions")
    results = relationship("SubmissionResult", back_populates="submission", cascade="all, delete-orphan")


class SubmissionResult(Base):
    __tablename__ = "submission_results"
    __table_args__ = (
        UniqueConstraint("submission_id", "test_case_id", name="uq_submission_result_case"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id"), nullable=False, index=True)
    test_case_id: Mapped[int | None] = mapped_column(
        ForeignKey("test_cases.id"),
        nullable=True,
        index=True,
    )
    verdict: Mapped[Verdict] = mapped_column(
        Enum(Verdict, name="verdict_enum"),
        nullable=False,
    )
    execution_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    memory_kb: Mapped[int | None] = mapped_column(Integer, nullable=True)
    message: Mapped[str | None] = mapped_column(Text, nullable=True)

    submission = relationship("Submission", back_populates="results")
    test_case = relationship("TestCase", back_populates="results")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)

    problems = relationship("ProblemTag", back_populates="tag", cascade="all, delete-orphan")


class ProblemTag(Base):
    __tablename__ = "problem_tags"
    __table_args__ = (
        UniqueConstraint("problem_id", "tag_id", name="uq_problem_tag"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    problem_id: Mapped[int] = mapped_column(ForeignKey("problems.id"), nullable=False, index=True)
    tag_id: Mapped[int] = mapped_column(ForeignKey("tags.id"), nullable=False, index=True)

    problem = relationship("Problem", back_populates="tags")
    tag = relationship("Tag", back_populates="problems")
