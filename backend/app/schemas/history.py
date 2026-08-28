from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HistoryEntry(BaseModel):
    id: str
    topic: str
    topic_type: str  # "letter" | "motion_sign"
    status: str  # pass, fail, no_attempt_detected
    correct: Optional[bool] = None
    confidence: Optional[float] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PracticeHistoryResponse(BaseModel):
    learner_id: str
    total_sessions: int
    scored_sessions: int
    accuracy_percent: Optional[float] = None
    entries: list[HistoryEntry]
