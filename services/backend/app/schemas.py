from pydantic import BaseModel
from typing import Optional


class CreateJobRequest(BaseModel):
    file_id: str
    prompt: Optional[str] = None
