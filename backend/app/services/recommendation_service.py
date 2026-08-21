from sqlalchemy.orm import Session

from app.services.learning_analytics_service import get_learner_analytics
from app.services.motion_sign_analytics_service import get_motion_sign_analytics

MAX_RECOMMENDATIONS = 5
RARE_ATTEMPT_THRESHOLD = 2  # fewer than this many attempts counts as "rarely practiced"
MASTERY_ACCURACY_THRESHOLD = 90.0
MASTERY_MIN_SCORED_ATTEMPTS = 3
WEAK_AREA_ACCURACY_THRESHOLD = 70.0
WEAK_AREA_MIN_SCORED_ATTEMPTS = 3


def _combined_topics(db: Session, learner_id: str) -> list[dict]:
    """
    Every practicable topic on the platform — static alphabet letters and
    motion signs (Wave/Clap) — as one flat list, each tagged with
    topic_type so downstream code (and the frontend, for routing to the
    right practice page) can tell them apart. Extend this list, not the
    tiering logic below, when a new topic_type (e.g. the vocabulary tier)
    gets its own attempt table.
    """
    analytics = get_learner_analytics(db, learner_id)
    motion_analytics = get_motion_sign_analytics(db, learner_id)

    topics = []
    for letter, stats in analytics["per_letter"].items():
        topics.append({"topic": letter, "topic_type": "letter", **stats})
    for sign, stats in motion_analytics["per_sign"].items():
        topics.append({"topic": sign, "topic_type": "motion_sign", **stats})
    return topics


def get_recommendations(db: Session, learner_id: str, topic_type: str | None = None) -> dict:
    """
    Builds a prioritized practice queue for a learner across every topic
    type on the platform, in priority order:
      1. weak_areas — struggling topics, worst accuracy first
      2. never-attempted topics — build a complete skill set
      3. rarely-attempted topics — attempted, but not enough to judge
      4. mastered topics — occasional retention/spaced-repetition review

    Later tiers only fill remaining slots after earlier ones, so mastery
    review only shows up when there isn't more pressing work.

    Pass topic_type="letter" or "motion_sign" to restrict the queue to one
    topic type — used by pages (like static-alphabet Practice) that can
    only act on one kind of topic and shouldn't be handed the other.
    Omit it (the Dashboard's overview widget does) to get the platform-wide
    mixed queue.
    """
    topics = _combined_topics(db, learner_id)
    if topic_type is not None:
        topics = [t for t in topics if t["topic_type"] == topic_type]

    candidates = []

    weak = [
        t for t in topics
        if t["accuracy_percent"] is not None
        and t["accuracy_percent"] < WEAK_AREA_ACCURACY_THRESHOLD
        and (t["correct"] + t["incorrect"]) >= WEAK_AREA_MIN_SCORED_ATTEMPTS
    ]
    weak.sort(key=lambda t: t["accuracy_percent"])
    for t in weak:
        scored = t["correct"] + t["incorrect"]
        candidates.append({
            "topic": t["topic"], "topic_type": t["topic_type"],
            "reason": f"weak area — {t['accuracy_percent']}% accuracy over {scored} attempts",
        })
    weak_keys = {(c["topic"], c["topic_type"]) for c in candidates}

    never_attempted = sorted(
        (t for t in topics if t["attempts"] == 0),
        key=lambda t: (t["topic_type"], t["topic"]),
    )
    for t in never_attempted:
        candidates.append({"topic": t["topic"], "topic_type": t["topic_type"], "reason": "not yet practiced"})

    rarely_attempted = sorted(
        (
            t for t in topics
            if (t["topic"], t["topic_type"]) not in weak_keys
            and 0 < t["attempts"] < RARE_ATTEMPT_THRESHOLD
        ),
        key=lambda t: (t["topic_type"], t["topic"]),
    )
    for t in rarely_attempted:
        candidates.append({
            "topic": t["topic"], "topic_type": t["topic_type"],
            "reason": f"rarely practiced — only {t['attempts']} attempt(s) so far",
        })

    mastered = sorted(
        (
            t for t in topics
            if t["accuracy_percent"] is not None
            and t["accuracy_percent"] >= MASTERY_ACCURACY_THRESHOLD
            and (t["correct"] + t["incorrect"]) >= MASTERY_MIN_SCORED_ATTEMPTS
        ),
        key=lambda t: (t["topic_type"], t["topic"]),
    )
    for t in mastered:
        candidates.append({
            "topic": t["topic"], "topic_type": t["topic_type"],
            "reason": f"reinforce mastery — {t['accuracy_percent']}% accuracy",
        })

    return {
        "learner_id": learner_id,
        "recommendations": candidates[:MAX_RECOMMENDATIONS],
    }
