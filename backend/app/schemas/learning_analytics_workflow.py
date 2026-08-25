from typing import List, Literal, Optional

from pydantic import BaseModel

TopicType = Literal["letter", "motion_sign"]


class CollectedDataSummary(BaseModel):
    total_letter_attempts: int
    total_motion_attempts: int
    total_scored_attempts: int


class WorkflowPerformanceMetrics(BaseModel):
    overall_accuracy_percent: Optional[float] = None
    letter_accuracy_percent: Optional[float] = None
    motion_sign_accuracy_percent: Optional[float] = None


class CourseCompletion(BaseModel):
    course_id: str
    title: str
    attempted_count: Optional[int] = None
    total_count: Optional[int] = None
    completion_percent: Optional[float] = None


class CompletionRate(BaseModel):
    overall_percent: Optional[float] = None
    attempted_count: int
    total_count: int
    by_course: List[CourseCompletion]


class FrequencyPatterns(BaseModel):
    days_active_total: int
    days_active_last_7: int
    days_active_last_30: int
    avg_attempts_per_active_day: Optional[float] = None
    last_active_date: Optional[str] = None
    days_since_last_active: Optional[int] = None
    most_active_weekday: Optional[str] = None


class CommonlyMissedItem(BaseModel):
    topic: str
    topic_type: TopicType
    incorrect_count: int
    accuracy_percent: Optional[float] = None


class AvoidedTopicItem(BaseModel):
    topic: str
    topic_type: TopicType


class PerformanceWindow(BaseModel):
    attempts: int
    scored_attempts: int
    accuracy_percent: Optional[float] = None


class PerformanceComparison(BaseModel):
    available: bool
    reason: Optional[str] = None
    current_period: PerformanceWindow
    previous_period: PerformanceWindow
    accuracy_delta_percent: Optional[float] = None
    trend: Optional[Literal["improving", "steady", "declining"]] = None


class LearningAnalyticsWorkflowResponse(BaseModel):
    learner_id: str
    collected_data_summary: CollectedDataSummary
    performance_metrics: WorkflowPerformanceMetrics
    completion_rate: CompletionRate
    frequency_patterns: FrequencyPatterns
    commonly_missed: List[CommonlyMissedItem]
    avoided_topics: List[AvoidedTopicItem]
    performance_comparison: PerformanceComparison
