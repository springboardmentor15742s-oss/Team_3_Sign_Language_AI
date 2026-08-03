from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class LearnerProfileResponse(BaseModel):
    id: int
    user_id: int
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    bio: Optional[str] = None
    learning_level: str
    preferred_language: str
    learning_goals: Optional[str] = None
    profile_picture_url: Optional[str] = None

    # Progress stats
    total_points: int
    current_streak: int
    completed_lessons_count: int
    last_active_at: datetime

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LearnerProfileUpdateRequest(BaseModel):
    full_name: Optional[str] = Field(None, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    bio: Optional[str] = None
    learning_level: Optional[str] = Field(None, description="beginner, intermediate, advanced")
    preferred_language: Optional[str] = Field(None, max_length=50)
    learning_goals: Optional[str] = None


class LearnerProgressUpdateRequest(BaseModel):
    total_points: Optional[int] = Field(None, ge=0)
    current_streak: Optional[int] = Field(None, ge=0)
    completed_lessons_count: Optional[int] = Field(None, ge=0)
