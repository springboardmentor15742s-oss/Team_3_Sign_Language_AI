from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class PracticeFeedbackResponse(BaseModel):
    # Null when status is no_attempt_detected — that outcome is not logged
    # as a PracticeAttempt, so there's no row to reference.
    attempt_id: Optional[str] = None
    status: str  # pass, fail, no_attempt_detected
    correct: Optional[bool] = None
    confidence: Optional[float] = None
    target_letter: str
    predicted_letter: Optional[str] = None
    feedback: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
