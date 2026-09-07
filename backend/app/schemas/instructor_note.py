from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

MAX_NOTE_LENGTH = 4000


class NoteCreate(BaseModel):
    note: str = Field(..., min_length=1, max_length=MAX_NOTE_LENGTH)


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
