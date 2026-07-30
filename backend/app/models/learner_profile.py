from sqlalchemy import Column, String, ForeignKey, DateTime
from datetime import datetime
from app.database import Base

class LearnerProfile(Base):
    __tablename__ = "learner_profiles"

    id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), unique=True, nullable=False)
    learning_level = Column(String, default="beginner")  # beginner, intermediate, advanced
    preferred_language = Column(String, default="ASL")   # ASL, ISL, etc.
    learning_goals = Column(String, nullable=True)        # free text goal description
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)