from typing import List, Optional

from pydantic import BaseModel

class LearnerRosterEntry(BaseModel):
    learner_id: str
    name: str
    email: str
    total_attempts: int
    overall_accuracy_percent: Optional[float] = None  # null when no scored attempts, never 0
    letters_scored: int
    total_letters: int
    weak_area_count: int

class LearnerRosterResponse(BaseModel):
    learners: List[LearnerRosterEntry]
