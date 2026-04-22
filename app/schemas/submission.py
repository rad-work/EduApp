from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SubmissionStatusResponse(BaseModel):
    id: int
    status: str
    language: str
    problem_id: int
    created_at: datetime
    queued_at: datetime | None
    finished_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
