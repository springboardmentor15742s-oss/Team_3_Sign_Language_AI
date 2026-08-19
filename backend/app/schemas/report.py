from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

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
    letter: str
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
