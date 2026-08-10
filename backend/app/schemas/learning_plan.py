from typing import List, Optional

from pydantic import BaseModel

class AreaStat(BaseModel):
    letter: str
    accuracy_percent: float
    scored_attempts: int

class PlanSummary(BaseModel):
    overall_accuracy_percent: Optional[float] = None
    total_attempts: int
    scored_attempts: int
    strongest_area: Optional[AreaStat] = None
    weakest_area: Optional[AreaStat] = None

class PracticeSessionLetter(BaseModel):
    order: int
    letter: str
    reason: str
    target_attempts: int

class PracticeSession(BaseModel):
    attempts_per_letter: int
    estimated_total_attempts: int
    letters: List[PracticeSessionLetter]

class LearningPlanResponse(BaseModel):
    learner_id: str
    summary: PlanSummary
    practice_session: PracticeSession
    motivational_note: str
