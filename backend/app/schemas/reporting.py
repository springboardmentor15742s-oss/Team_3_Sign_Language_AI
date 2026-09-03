from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel

from app.schemas.instructor import WeakLetterCount


class ClassReportRosterEntry(BaseModel):
    learner_id: str
    name: str
    email: str
    total_attempts: int
    overall_accuracy_percent: Optional[float] = None  # null when no scored attempts, never 0


class ClassReportResponse(BaseModel):
    # "roster" = an instructor's own class; "platform" = every learner
    # (admin scope) — same instructor_id=None convention as everywhere
    # else, just spelled out here since a report is read outside the app.
    scope: Literal["roster", "platform"]
    generated_at: datetime

    learner_count: int
    active_learner_count: int
    average_accuracy_percent: Optional[float] = None
    weak_letter_distribution: List[WeakLetterCount]
    completed_assignment_count: int
    outstanding_assignment_count: int

    roster: List[ClassReportRosterEntry]


class AssignmentReportRow(BaseModel):
    learner_id: str
    learner_name: str
    learner_email: str
    topic: str
    topic_type: str
    notes: Optional[str] = None
    due_date: Optional[str] = None
    completed: bool
    completed_at: Optional[datetime] = None
    overdue: bool
    created_at: datetime


class AssignmentReportResponse(BaseModel):
    scope: Literal["roster", "platform"]
    generated_at: datetime

    total_count: int
    completed_count: int
    outstanding_count: int
    overdue_count: int

    rows: List[AssignmentReportRow]
