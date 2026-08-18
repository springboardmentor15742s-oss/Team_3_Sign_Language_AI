from sqlalchemy.orm import Session

from app.services.learning_analytics_service import get_learner_analytics

MAX_RECOMMENDATIONS = 5
RARE_ATTEMPT_THRESHOLD = 2  # fewer than this many attempts counts as "rarely practiced"
MASTERY_ACCURACY_THRESHOLD = 90.0
MASTERY_MIN_SCORED_ATTEMPTS = 3


def get_recommendations(db: Session, learner_id: str) -> dict:
    """
    Builds a prioritized practice queue for a learner from their
    learning_analytics_service stats, in priority order:
      1. weak_areas — struggling letters, worst accuracy first
      2. never-attempted letters — build a complete skill set
      3. rarely-attempted letters — attempted, but not enough to judge
      4. mastered letters — occasional retention/spaced-repetition review

    Later tiers only fill remaining slots after earlier ones, so
    mastery review only shows up when there isn't more pressing work.
    """
    analytics = get_learner_analytics(db, learner_id)
    per_letter = analytics["per_letter"]

    candidates = []

    for weak in analytics["weak_areas"]:
        candidates.append({
            "letter": weak["letter"],
            "reason": f"weak area — {weak['accuracy_percent']}% accuracy over {weak['scored_attempts']} attempts",
        })
    weak_letters = {c["letter"] for c in candidates}

    # per_letter covers all supported letters (learning_analytics_service
    # backfills unattempted ones with attempts=0), so "never attempted" is
    # attempts == 0, not absence from the dict.
    never_attempted = sorted(
        letter for letter, stats in per_letter.items() if stats["attempts"] == 0
    )
    for letter in never_attempted:
        candidates.append({"letter": letter, "reason": "not yet practiced"})

    rarely_attempted = sorted(
        letter for letter, stats in per_letter.items()
        if letter not in weak_letters and 0 < stats["attempts"] < RARE_ATTEMPT_THRESHOLD
    )
    for letter in rarely_attempted:
        attempts = per_letter[letter]["attempts"]
        candidates.append({
            "letter": letter,
            "reason": f"rarely practiced — only {attempts} attempt(s) so far",
        })

    mastered = sorted(
        letter for letter, stats in per_letter.items()
        if stats["accuracy_percent"] is not None
        and stats["accuracy_percent"] >= MASTERY_ACCURACY_THRESHOLD
        and (stats["correct"] + stats["incorrect"]) >= MASTERY_MIN_SCORED_ATTEMPTS
    )
    for letter in mastered:
        accuracy = per_letter[letter]["accuracy_percent"]
        candidates.append({"letter": letter, "reason": f"reinforce mastery — {accuracy}% accuracy"})

    return {
        "learner_id": learner_id,
        "recommendations": candidates[:MAX_RECOMMENDATIONS],
    }
