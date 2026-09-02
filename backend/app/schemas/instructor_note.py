from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NoteCreate(BaseModel):
    note: str


class NoteResponse(BaseModel):
    id: str
    learner_id: str
    instructor_id: str
    instructor_name: Optional[str] = None
    note: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    notes: list[NoteResponse]
