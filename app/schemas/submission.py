from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SubmissionCreateRequest(BaseModel):
    problem_id: int
    language: str = Field(min_length=1, max_length=32)
    source_code: str = Field(min_length=1)


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
