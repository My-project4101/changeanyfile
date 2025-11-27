# services/backend/app/models.py
from sqlmodel import SQLModel, Field
from typing import Optional
import datetime
import uuid


def now_ts() -> int:
    return int(datetime.datetime.utcnow().timestamp())


class Job(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(default_factory=lambda: str(uuid.uuid4()), index=True, unique=True)
    file_id: str
    original_name: str
    prompt: Optional[str] = None

    status: str = Field(default="queued")  # queued | processing | completed | failed
    result_filename: Optional[str] = None
    result_path: Optional[str] = None
    result_size: Optional[int] = None

    created_at: int = Field(default_factory=now_ts)
    updated_at: int = Field(default_factory=now_ts)


class JobLog(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_id: str = Field(index=True)
    created_at: int = Field(default_factory=now_ts)
    message: str
