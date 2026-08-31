from sqlalchemy import Column, String, ForeignKey, Boolean, Float, DateTime
from datetime import datetime
from app.database import Base

class MotionSignAttempt(Base):
    """
    Separate table from PracticeAttempt (static alphabet) because motion
    signs are scored differently: there's no trained-model confidence
    here, just a rule-based pass/fail against hand-trajectory geometry
    over a short frame sequence (see motion_sign_service.py). Keeping the
    tables apart means the alphabet accuracy/streak stats in
    progress_service.py never mix with this different kind of attempt.
    """

    __tablename__ = "motion_sign_attempts"

    id = Column(String, primary_key=True)
    learner_id = Column(String, ForeignKey("users.id"), nullable=False)
    target_sign = Column(String, nullable=False)
    predicted_sign = Column(String, nullable=True)  # null when no match / no hand(s) detected
    status = Column(String, nullable=False)  # pass, fail, no_attempt_detected
    correct = Column(Boolean, nullable=True)  # True/False, or null for no_attempt_detected
    # Always null today: the rule-based detector below produces a boolean
    # match, not a calibrated probability, so a confidence number here
    # would be fabricated. Kept nullable (not dropped) so a future trained
    # sequence model — e.g. for the real ASL vocabulary tiers — can start
    # populating it without a schema change.
    confidence = Column(Float, nullable=True)
    frame_count = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
