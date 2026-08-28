from typing import List, Literal, Optional

from pydantic import BaseModel

# Mirrors app/schemas/recommendation.py and adaptive_learning.py's TopicType /
# LearningLevel literals — kept in sync deliberately, not re-derived.
TopicType = Literal["letter", "motion_sign"]
LearningLevel = Literal["beginner", "intermediate", "advanced"]
Status = Literal["pass", "fail", "no_attempt_detected"]


class ActivityFeedback(BaseModel):
    """Structured, tiered feedback for one just-completed activity attempt."""

    topic: str
    topic_type: TopicType
    status: Status
    learner_level: LearningLevel
    message: str
    performance: str
    error: Optional[str] = None
    improvement_tip: Optional[str] = None


class FeedbackErrorItem(BaseModel):
    topic: str
    topic_type: TopicType
    accuracy_percent: Optional[float] = None
    scored_attempts: Optional[int] = None
    detail: str


class FeedbackPerformance(BaseModel):
    learning_level: LearningLevel
    overall_accuracy_percent: Optional[float] = None
    scored_attempts: int
    summary: str


class FeedbackActivity(BaseModel):
    type: Literal["lesson", "exercise", "quiz", "practice", "revision", "challenge"]
    difficulty: Literal["beginner", "intermediate", "advanced"]
    topic: str
    instruction: str


class FeedbackImprovementArea(BaseModel):
    topic: str
    topic_type: TopicType
    accuracy_percent: Optional[float] = None
    suggested_activities: List[FeedbackActivity] = []


class LearnerFeedbackResponse(BaseModel):
    """Aggregate, dashboard-facing feedback: errors, performance, and areas for improvement, tiered by skill level."""

    learner_id: str
    learner_level: LearningLevel
    generated_from_attempts: int
    errors: List[FeedbackErrorItem]
    performance: FeedbackPerformance
    areas_for_improvement: List[FeedbackImprovementArea]
