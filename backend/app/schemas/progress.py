from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class Achievement(BaseModel):
    id: str
    label: str
    description: str
    unlocked: bool
    progress_current: float
    progress_target: float


class RecentActivityItem(BaseModel):
    letter: str
    status: str  # pass, fail, no_attempt_detected
    confidence: Optional[float] = None
    created_at: Optional[datetime] = None


class PerformanceForecast(BaseModel):
    available: bool
    # Set only when available is False, explaining what's missing.
    reason: Optional[str] = None
    current_level: Optional[str] = None
    predicted_next_level: Optional[str] = None
    trend_percent_per_day: Optional[float] = None
    estimated_days_to_next_level: Optional[int] = None


class LearnerProgressResponse(BaseModel):
    learner_id: str
    current_streak_days: int
    achievements: list[Achievement]
    recent_activity: list[RecentActivityItem]
    forecast: PerformanceForecast
