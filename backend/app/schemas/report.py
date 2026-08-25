from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel

from app.schemas.learning_analytics_workflow import LearningAnalyticsWorkflowResponse

class ReportLetterStats(BaseModel):
    letter: str
    attempts: int
    accuracy_percent: Optional[float] = None  # null when untried, never 0

class ReportWeakArea(BaseModel):
    letter: str
    accuracy_percent: float
    scored_attempts: int
    note: str  # feedback_service's own corrective message, not new copy

class ReportRecommendation(BaseModel):
    # topic/topic_type (not "letter") since recommendation_service's queue
    # is combined across letters AND motion signs — fixed here to match
    # what get_recommendations() actually returns (this previously only
    # had a `letter` field left over from before that combined-topics
    # change, which meant building this report raised a validation error
    # for any learner with a non-empty recommendations queue).
    topic: str
    topic_type: Literal["letter", "motion_sign"]
    reason: str

class ReportConfusionPair(BaseModel):
    target_letter: str
    predicted_letter: str
    count: int

class LearnerReport(BaseModel):
    learner_id: str
    learner_name: str
    learner_email: str
    generated_at: datetime

    total_attempts: int
    scored_attempts: int
    overall_accuracy_percent: Optional[float] = None  # null when nothing scored yet, never 0
    letters_scored: int
    total_letters: int

    per_letter: List[ReportLetterStats]
    weak_areas: List[ReportWeakArea]
    recommendations: List[ReportRecommendation]
    confusion_pairs: List[ReportConfusionPair]

    # Carried through from learning_analytics_service so the PDF can state
    # the actual threshold in prose without a second hardcoded copy of it.
    weak_area_accuracy_threshold: float
    weak_area_min_scored_attempts: int

    # Task 2 — learning analytics workflow: completion rate, activity
    # frequency patterns, commonly-missed/avoided topics, and a
    # current-vs-previous performance comparison, computed by
    # learning_analytics_workflow_service and embedded here so the one
    # downloadable report contains everything the brief asked for.
    analytics_workflow: LearningAnalyticsWorkflowResponse
