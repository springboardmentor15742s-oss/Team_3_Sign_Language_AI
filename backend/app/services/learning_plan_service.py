from sqlalchemy.orm import Session

from app.services.learning_analytics_service import get_learner_analytics
from app.services.recommendation_service import get_recommendations

ATTEMPTS_PER_LETTER = 3


def _pick_strongest_and_weakest(per_letter: dict) -> tuple[dict | None, dict | None]:
    scored_letters = [
        {
            "letter": letter,
            "accuracy_percent": stats["accuracy_percent"],
            "scored_attempts": stats["correct"] + stats["incorrect"],
        }
        for letter, stats in per_letter.items()
        if stats["accuracy_percent"] is not None
    ]
    if not scored_letters:
        return None, None

    strongest = max(scored_letters, key=lambda s: s["accuracy_percent"])
    weakest = min(scored_letters, key=lambda s: s["accuracy_percent"])
    return strongest, weakest


def _build_summary(analytics: dict) -> dict:
    strongest, weakest = _pick_strongest_and_weakest(analytics["per_letter"])
    return {
        "overall_accuracy_percent": analytics["overall_accuracy_percent"],
        "total_attempts": analytics["total_attempts"],
        "scored_attempts": analytics["scored_attempts"],
        "strongest_area": strongest,
        "weakest_area": weakest,
    }


def _build_practice_session(recommendations: list[dict]) -> dict:
    # recommendations here is always topic_type="letter"-filtered (see
    # generate_learning_plan below) — this practice session's schema is
    # letter-specific (PracticeSessionLetter, attempts_per_letter), so a
    # motion-sign topic has no "letter" to show here.
    return {
        "attempts_per_letter": ATTEMPTS_PER_LETTER,
        "estimated_total_attempts": len(recommendations) * ATTEMPTS_PER_LETTER,
        "letters": [
            {
                "order": i + 1,
                "letter": rec["topic"],
                "reason": rec["reason"],
                "target_attempts": ATTEMPTS_PER_LETTER,
            }
            for i, rec in enumerate(recommendations)
        ],
    }


def _build_motivational_note(analytics: dict) -> str:
    """
    Grounds the note in what the data actually shows rather than
    generic praise: references a real accuracy trend when there's more
    than one day of history to compare, and otherwise stays neutral
    instead of fabricating an "improvement" claim from a single day of
    data (which is exactly the current test learner's situation).
    """
    total_attempts = analytics["total_attempts"]
    if total_attempts == 0:
        return "You haven't logged any practice attempts yet — start with a few letters to get a baseline."

    scored_days = [d for d in analytics["accuracy_trend"] if d["accuracy_percent"] is not None]
    if len(scored_days) >= 2:
        first, last = scored_days[0], scored_days[-1]
        delta = last["accuracy_percent"] - first["accuracy_percent"]
        if delta > 0:
            return (
                f"Your accuracy improved from {first['accuracy_percent']}% on {first['date']} "
                f"to {last['accuracy_percent']}% on {last['date']} — keep it up."
            )
        if delta < 0:
            return (
                f"Your accuracy dipped from {first['accuracy_percent']}% on {first['date']} "
                f"to {last['accuracy_percent']}% on {last['date']} — that's normal, stay consistent."
            )
        return f"Your accuracy has held steady at {last['accuracy_percent']}% across your practice days."

    if analytics["overall_accuracy_percent"] is None:
        return (
            f"You've logged {total_attempts} attempt(s) so far — none scored yet since your hand wasn't "
            "detected. Try repositioning in frame and give it another go."
        )

    return (
        f"You've logged {total_attempts} attempt(s) so far with {analytics['overall_accuracy_percent']}% "
        "accuracy. Keep practicing across a few more days and we'll start tracking your trend."
    )


def generate_learning_plan(db: Session, learner_id: str) -> dict:
    """
    Builds a personalized practice plan: a summary of current standing,
    a sequenced practice session pulled from the recommendation queue,
    and an honest, data-grounded motivational note.

    Filtered to topic_type="letter" — this plan's practice_session schema
    is letter-specific (PracticeSessionLetter), so a mixed queue including
    motion signs would have nowhere valid to put a "Wave" recommendation.
    """
    analytics = get_learner_analytics(db, learner_id)
    recommendations = get_recommendations(db, learner_id, topic_type="letter")["recommendations"]

    return {
        "learner_id": learner_id,
        "summary": _build_summary(analytics),
        "practice_session": _build_practice_session(recommendations),
        "motivational_note": _build_motivational_note(analytics),
    }
