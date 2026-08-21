from typing import List, Literal, Optional

from pydantic import BaseModel

TopicType = Literal["letter", "motion_sign"]


class TopicProgress(BaseModel):
    topic: str
    topic_type: TopicType
    accuracy_percent: Optional[float] = None
    scored_attempts: int
    trend: Literal["improving", "steady", "declining", "insufficient_data"]


class AdaptiveActivity(BaseModel):
    type: Literal["lesson", "exercise", "quiz", "practice", "revision", "challenge"]
    difficulty: Literal["basic", "intermediate", "advanced"]
    topic: str
    instruction: str


class AdaptiveRecommendation(BaseModel):
    topic: str
    topic_type: TopicType
    priority: int
    reason: str
    activities: List[AdaptiveActivity]


class AdaptiveLearningPlanResponse(BaseModel):
    learner_id: str
    learning_level: Literal["beginner", "intermediate", "advanced"]
    profile_summary: str
    overall_accuracy_percent: Optional[float] = None
    activity_days: int
    time_spent_minutes: float
    completed_topics: List[str]
    strong_topics: List[TopicProgress]
    weak_topics: List[TopicProgress]
    needs_more_practice: List[TopicProgress]
    recommendations: List[AdaptiveRecommendation]
    next_assessment: str
