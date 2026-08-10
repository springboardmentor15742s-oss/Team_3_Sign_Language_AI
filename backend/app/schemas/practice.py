from datetime import datetime
from typing import Optional

from pydantic import BaseModel

class PracticeFeedbackResponse(BaseModel):
    attempt_id: str
    status: str  # pass, fail, no_attempt_detected
    correct: Optional[bool] = None
    confidence: Optional[float] = None
    target_letter: str
    predicted_letter: Optional[str] = None
    feedback: str
    created_at: datetime

    class Config:
        from_attributes = True
