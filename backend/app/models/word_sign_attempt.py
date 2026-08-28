from sqlalchemy import Column, String, ForeignKey, Boolean, Float, DateTime
from datetime import datetime
from app.database import Base


class WordSignAttempt(Base):
    """
    Attempts for the Intermediate Conversational Fluency vocabulary —
    real trained-model predictions (msasl_intermediate_classifier.pkl,
    16 words with enough real MS-ASL clips per word — see
    scripts/train_msasl_classifier.py for why the other 14 candidate
    words were dropped rather than shipped on too little data), unlike
    motion_sign_attempts' rule-based Wave/Clap detection. Kept as its
    own table rather than folded into practice_attempts (alphabet) or
    motion_sign_attempts (gestures) because it's a distinct topic type
    with its own vocabulary and its own model — same reasoning as why
    those two don't share a table with each other.
    """

    __tablename__ = "word_sign_attempts"

    id = Column(String, primary_key=True)
    learner_id = Column(String, ForeignKey("users.id"), nullable=False)
    target_word = Column(String, nullable=False)
    predicted_word = Column(String, nullable=True)  # null only for no_attempt_detected
    status = Column(String, nullable=False)  # pass, fail, no_attempt_detected
    correct = Column(Boolean, nullable=True)
    # Real predict_proba() output from the trained classifier for its
    # top prediction — not fabricated, but should be read as "how sure
    # the model was," not "how likely this is correct": with test
    # accuracy at 49% (see the model bundle's test_accuracy field) the
    # model is meaningfully better than chance across 16 words but far
    # from reliable, and its probabilities aren't independently
    # calibrated against that number.
    confidence = Column(Float, nullable=True)
    frame_count = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
