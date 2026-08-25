from sqlalchemy.orm import Session

from app.models.learning_activity import LearningActivity


def record_practice_activity(db: Session, learner_id: str, topic: str, duration_seconds: float | None) -> None:
    """Store the learner-reported active practice time with safe bounds.

    The browser timer is an approximation, so it is used for learner insight
    only—not for grading or recommendation priority.
    """
    duration = max(0.0, min(float(duration_seconds or 0), 60 * 60))
    db.add(LearningActivity(
        learner_id=learner_id,
        activity_type="practice",
        topic=topic,
        duration_seconds=duration,
    ))
    db.commit()
