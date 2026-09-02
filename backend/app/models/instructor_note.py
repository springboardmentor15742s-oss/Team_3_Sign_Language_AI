from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from datetime import datetime
from app.database import Base


class InstructorNote(Base):
    """
    A freeform note an instructor leaves on a learner's profile — e.g.
    context from a in-person session, a reminder for next time, an
    observation that doesn't fit the topic-only assignment model. Visible
    to any staff viewing that learner (same require_self_or_staff-style
    audience as the rest of the instructor-facing data), but never
    exposed through the learner's own /api/learner/... routes — this is
    staff-facing context, not feedback delivered to the learner. If a
    learner-visible note is ever wanted, that's a deliberate new feature,
    not a visibility toggle on this one.
    """

    __tablename__ = "instructor_notes"

    id = Column(String, primary_key=True)
    instructor_id = Column(String, ForeignKey("users.id"), nullable=False)
    learner_id = Column(String, ForeignKey("users.id"), nullable=False)
    note = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
