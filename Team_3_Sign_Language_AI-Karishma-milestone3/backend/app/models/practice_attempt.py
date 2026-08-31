from sqlalchemy import Column, String, ForeignKey, Boolean, Float, DateTime
from datetime import datetime
from app.database import Base

class PracticeAttempt(Base):
    __tablename__ = "practice_attempts"

    id = Column(String, primary_key=True)
    learner_id = Column(String, ForeignKey("users.id"), nullable=False)
    target_letter = Column(String, nullable=False)
    predicted_letter = Column(String, nullable=True)  # null when no hand was detected
    status = Column(String, nullable=False)  # pass, fail, no_attempt_detected
    correct = Column(Boolean, nullable=True)  # True/False, or null for no_attempt_detected
    confidence = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
