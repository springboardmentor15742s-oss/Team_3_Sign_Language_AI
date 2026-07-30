from pydantic import BaseModel
from typing import Optional

class LearnerProfileUpdate(BaseModel):
    learning_level: Optional[str] = None
    preferred_language: Optional[str] = None
    learning_goals: Optional[str] = None

class LearnerProfileResponse(BaseModel):
    id: str
    user_id: str
    learning_level: str
    preferred_language: str
    learning_goals: Optional[str] = None

    class Config:
        from_attributes = True