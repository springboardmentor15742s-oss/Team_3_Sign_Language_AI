from typing import Optional

from pydantic import BaseModel


class RosterAccuracyTrendPoint(BaseModel):
    date: str
    attempts: int
    scored_attempts: int
    accuracy_percent: Optional[float] = None


class RosterCourseCompletion(BaseModel):
    course_id: str
    course_title: str
    learner_count: int
    not_started_count: int
    in_progress_count: int
    completed_count: int
    certified_count: Optional[int] = None


class ClassTrendsResponse(BaseModel):
    accuracy_trend: list[RosterAccuracyTrendPoint]
    course_completion: list[RosterCourseCompletion]
