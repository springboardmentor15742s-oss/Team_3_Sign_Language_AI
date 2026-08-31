from sqlalchemy.orm import Session

from app.models.user import User
from app.services.gesture_recognition_service import get_supported_letters
from app.services.learning_analytics_service import get_learner_analytics


def get_learner_roster(db: Session) -> list[dict]:
    """
    Builds a read-only roster for instructors: every learner in the
    system with lifetime stats. Reuses learning_analytics_service for
    every learner rather than re-deriving accuracy/weak-area math here,
    so the weak-area threshold stays defined in exactly one place.

    A learner with zero attempts still appears, with
    overall_accuracy_percent=None (never 0) — get_learner_analytics
    already preserves that distinction.
    """
    total_letters = len(get_supported_letters())
    learners = db.query(User).filter(User.role == "learner").all()

    roster = []
    for learner in learners:
        analytics = get_learner_analytics(db, learner.id)
        letters_scored = sum(
            1 for stats in analytics["per_letter"].values() if stats["accuracy_percent"] is not None
        )
        roster.append({
            "learner_id": learner.id,
            "name": learner.name,
            "email": learner.email,
            "total_attempts": analytics["total_attempts"],
            "overall_accuracy_percent": analytics["overall_accuracy_percent"],
            "letters_scored": letters_scored,
            "total_letters": total_letters,
            "weak_area_count": len(analytics["weak_areas"]),
        })

    return roster
