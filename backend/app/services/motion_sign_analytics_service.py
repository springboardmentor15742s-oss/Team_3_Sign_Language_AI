from sqlalchemy.orm import Session

from app.models.motion_sign_attempt import MotionSignAttempt
from app.services.motion_sign_service import SUPPORTED_MOTION_SIGNS

# Same thresholds as learning_analytics_service, kept independent (not
# imported) so the two topic types can be tuned separately if their
# attempt volume/difficulty ever diverges.
WEAK_AREA_ACCURACY_THRESHOLD = 70.0
WEAK_AREA_MIN_SCORED_ATTEMPTS = 3


def get_motion_sign_analytics(db: Session, learner_id: str) -> dict:
    """
    Aggregates a learner's MotionSignAttempt history into the same shape
    learning_analytics_service produces for letters (per_sign, weak_areas,
    overall accuracy), so the recommendation/adaptive-learning engines can
    treat letters and motion signs as one combined topic pool.

    per_sign always covers all of SUPPORTED_MOTION_SIGNS, not just signs
    the learner has tried — unattempted signs appear with attempts=0 and
    accuracy_percent=None, mirroring per_letter's convention.
    """
    attempts = (
        db.query(MotionSignAttempt)
        .filter(MotionSignAttempt.learner_id == learner_id)
        .order_by(MotionSignAttempt.created_at.asc())
        .all()
    )

    per_sign = {
        sign: {"attempts": 0, "correct": 0, "incorrect": 0, "no_attempt": 0, "accuracy_percent": None}
        for sign in SUPPORTED_MOTION_SIGNS
    }
    for attempt in attempts:
        stats = per_sign.setdefault(
            attempt.target_sign,
            {"attempts": 0, "correct": 0, "incorrect": 0, "no_attempt": 0, "accuracy_percent": None},
        )
        stats["attempts"] += 1
        if attempt.status == "no_attempt_detected":
            stats["no_attempt"] += 1
        elif attempt.correct:
            stats["correct"] += 1
        else:
            stats["incorrect"] += 1

    for stats in per_sign.values():
        scored = stats["correct"] + stats["incorrect"]
        stats["accuracy_percent"] = round(stats["correct"] / scored * 100, 1) if scored else None

    per_sign = dict(sorted(per_sign.items()))

    weak_areas = [
        {
            "sign": sign,
            "accuracy_percent": stats["accuracy_percent"],
            "scored_attempts": stats["correct"] + stats["incorrect"],
        }
        for sign, stats in per_sign.items()
        if stats["accuracy_percent"] is not None
        and stats["accuracy_percent"] < WEAK_AREA_ACCURACY_THRESHOLD
        and (stats["correct"] + stats["incorrect"]) >= WEAK_AREA_MIN_SCORED_ATTEMPTS
    ]
    weak_areas.sort(key=lambda w: w["accuracy_percent"])

    total_attempts = sum(s["attempts"] for s in per_sign.values())
    correct_count = sum(s["correct"] for s in per_sign.values())
    incorrect_count = sum(s["incorrect"] for s in per_sign.values())
    scored_attempts = correct_count + incorrect_count
    overall_accuracy_percent = round(correct_count / scored_attempts * 100, 1) if scored_attempts else None

    return {
        "learner_id": learner_id,
        "total_attempts": total_attempts,
        "correct_count": correct_count,
        "incorrect_count": incorrect_count,
        "scored_attempts": scored_attempts,
        "overall_accuracy_percent": overall_accuracy_percent,
        "per_sign": per_sign,
        "weak_areas": weak_areas,
    }
