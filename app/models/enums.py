from enum import StrEnum


class UserRole(StrEnum):
    ADMIN = "admin"
    USER = "user"


class SubmissionStatus(StrEnum):
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Verdict(StrEnum):
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    RUNTIME_ERROR = "runtime_error"
    COMPILATION_ERROR = "compilation_error"
    PRESENTATION_ERROR = "presentation_error"
    SYSTEM_ERROR = "system_error"
