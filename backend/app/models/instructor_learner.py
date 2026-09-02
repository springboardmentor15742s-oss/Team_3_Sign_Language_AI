from sqlalchemy import Column, String, DateTime, ForeignKey, UniqueConstraint
from datetime import datetime
from app.database import Base


class InstructorLearner(Base):
    """
    Roster ownership: which learners a given instructor actually manages.
    Before this existed, every instructor could see and assign to every
    learner in the system — that flat model doesn't scale past a single
    demo class, so this table is the join that scopes the roster page,
    class-wide analytics, and new-assignment creation to "my learners"
    for the instructor role. Admins are intentionally exempt everywhere
    this table is consulted (see instructor_service.get_learner_roster
    and instructor.py's ownership check) — they keep seeing everyone,
    since they're not "a" class's instructor.

    One row per (instructor, learner) pair; the unique constraint makes
    "add a learner already on your roster" a safe no-op rather than a
    duplicate row.
    """

    __tablename__ = "instructor_learners"

    id = Column(String, primary_key=True)
    instructor_id = Column(String, ForeignKey("users.id"), nullable=False)
    learner_id = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("instructor_id", "learner_id", name="uq_instructor_learner"),
    )
