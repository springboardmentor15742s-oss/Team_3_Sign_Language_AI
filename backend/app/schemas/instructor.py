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

class AddLearnerRequest(BaseModel):
    # The instructor adds a learner to their roster by email rather than
    # by id, since that's what an instructor actually knows about a
    # learner — ids are internal.
    learner_email: str

class WeakLetterCount(BaseModel):
    letter: str
    learner_count: int  # how many of this instructor's learners have this letter as a weak area

class ClassAnalyticsResponse(BaseModel):
    learner_count: int
    active_learner_count: int  # learners with at least one attempt
    average_accuracy_percent: Optional[float] = None  # null when no learner has a scored attempt yet
    weak_letter_distribution: List[WeakLetterCount]
    outstanding_assignment_count: int
    completed_assignment_count: int
