from typing import Dict, List, Optional

from pydantic import BaseModel

class LetterStats(BaseModel):
    attempts: int
    correct: int
    incorrect: int
    no_attempt: int
    accuracy_percent: Optional[float] = None

class AccuracyTrendPoint(BaseModel):
    date: str
    attempts: int
    scored_attempts: int
    correct: int
    accuracy_percent: Optional[float] = None

class LetterCount(BaseModel):
    letter: str
    attempts: int

class WeakArea(BaseModel):
    letter: str
    accuracy_percent: float
    scored_attempts: int

class LearnerAnalyticsResponse(BaseModel):
    learner_id: str
    total_attempts: int
    correct_count: int
    incorrect_count: int
    no_attempt_count: int
    scored_attempts: int
    overall_accuracy_percent: Optional[float] = None
    accuracy_trend: List[AccuracyTrendPoint]
    per_letter: Dict[str, LetterStats]
    most_practiced_letters: List[LetterCount]
    least_practiced_letters: List[LetterCount]
    weak_areas: List[WeakArea]
