from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.languages import normalize_submission_language


class SubmissionCreateRequest(BaseModel):
    problem_id: int
    language: str = Field(min_length=1, max_length=32)
    source_code: str = Field(min_length=1)

    @field_validator("language")
    @classmethod
    def validate_language(cls, value: str) -> str:
        normalized = normalize_submission_language(value)
        if not normalized:
            raise ValueError("Unsupported language")
        return normalized


class SubmissionStatusResponse(BaseModel):
    id: int
    status: str
    language: str
    problem_id: int
    created_at: datetime
    queued_at: datetime | None
    finished_at: datetime | None
    verdict: str | None = None
    message: str | None = None
    is_final: bool

    model_config = ConfigDict(from_attributes=True)
