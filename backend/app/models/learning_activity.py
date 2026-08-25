from datetime import datetime
import uuid

from sqlalchemy import Column, DateTime, Float, ForeignKey, String

from app.database import Base


class LearningActivity(Base):
    """Completed learner activity, kept separate from the assessment result."""

    __tablename__ = "learning_activities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    learner_id = Column(String, ForeignKey("users.id"), nullable=False, index=True)
    activity_type = Column(String, nullable=False)  # currently: practice
    topic = Column(String, nullable=False)
    duration_seconds = Column(Float, nullable=False, default=0)
    completed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
