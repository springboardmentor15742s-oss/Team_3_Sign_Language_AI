"""Data-driven, continuously refreshed learning recommendations.

The engine deliberately does not persist a static path. It rebuilds a learner's
profile from their latest stored assessment attempts on every request, so the
next recommendation changes immediately after a new assessment is saved.

Covers every scored activity type on the platform as one combined topic
pool — static alphabet letters (PracticeAttempt) and motion signs like
Wave/Clap (MotionSignAttempt) — rather than two separate engines, so a
learner's overall level and priority queue reflect everything they've
practiced, not just letters. Extend TOPIC_LABELS and the topics_data build
in get_adaptive_learning_plan, not the tiering/activity logic below, when a
new topic_type (e.g. the vocabulary tier) gets its own attempt table.
"""

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.practice_attempt import PracticeAttempt
from app.models.motion_sign_attempt import MotionSignAttempt
from app.models.learning_activity import LearningActivity
from app.services.learning_analytics_service import get_learner_analytics
from app.services.motion_sign_analytics_service import get_motion_sign_analytics

MIN_EVIDENCE = 3
RECENT_WINDOW = 3
MAX_TOPICS = 3

# Word used in activity instructions in place of "handshape" for topic
# types where that word wouldn't make sense (a motion sign isn't a static
# shape). Falls back to "topic" for any topic_type not listed here.
TOPIC_LABELS = {"letter": "handshape", "motion_sign": "motion"}


def _accuracy(results: list[bool]) -> float | None:
    if not results:
        return None
    return round(sum(results) / len(results) * 100, 1)


def _trend(results: list[bool]) -> str:
    if len(results) < MIN_EVIDENCE * 2:
        return "insufficient_data"
    earlier = _accuracy(results[-(RECENT_WINDOW * 2):-RECENT_WINDOW])
    recent = _accuracy(results[-RECENT_WINDOW:])
    if recent - earlier >= 15:
        return "improving"
    if earlier - recent >= 15:
        return "declining"
    return "steady"


def _level(overall_accuracy: float | None, scored_attempts: int) -> str:
    # A very small sample should start with the supportive beginner route;
    # this avoids declaring someone advanced after one lucky capture.
    if scored_attempts < MIN_EVIDENCE or overall_accuracy is None or overall_accuracy < 60:
        return "beginner"
    if overall_accuracy < 85:
        return "intermediate"
    return "advanced"


def _activities(topic: str, topic_type: str, level: str, accuracy: float | None, trend: str) -> list[dict]:
    label = TOPIC_LABELS.get(topic_type, "topic")

    if accuracy is None:
        return [
            {"type": "lesson", "difficulty": "beginner", "topic": topic, "instruction": f"Learn the {topic} {label} and its key landmarks."},
            {"type": "practice", "difficulty": "beginner", "topic": topic, "instruction": f"Complete three guided {topic} captures to establish a baseline."},
            {"type": "quiz", "difficulty": "beginner", "topic": topic, "instruction": f"Take a short {topic} assessment after the guided practice."},
        ]

    if accuracy < 60:
        if level == "beginner":
            return [
                {"type": "lesson", "difficulty": "beginner", "topic": topic, "instruction": f"Review the basic {topic} {label} before practising."},
                {"type": "exercise", "difficulty": "beginner", "topic": topic, "instruction": f"Complete slow, guided {topic} exercises."},
                {"type": "quiz", "difficulty": "beginner", "topic": topic, "instruction": f"Retake an easy {topic} check after three captures."},
            ]
        return [
            {"type": "revision", "difficulty": "intermediate", "topic": topic, "instruction": f"Revisit the {topic} concept and compare it with similar {label}s."},
            {"type": "exercise", "difficulty": "advanced", "topic": topic, "instruction": f"Complete challenging {topic} discrimination exercises."},
            {"type": "quiz", "difficulty": "advanced", "topic": topic, "instruction": f"Take an advanced {topic} assessment to confirm recovery."},
        ]

    if accuracy < 85:
        focus = "Maintain the improving pattern" if trend == "improving" else "Strengthen consistency"
        return [
            {"type": "practice", "difficulty": "intermediate", "topic": topic, "instruction": f"{focus} with three targeted {topic} attempts."},
            {"type": "exercise", "difficulty": "intermediate", "topic": topic, "instruction": f"Practise {topic} alongside visually similar {label}s."},
            {"type": "quiz", "difficulty": "intermediate", "topic": topic, "instruction": f"Take an intermediate {topic} quiz after practice."},
        ]

    return [
        {"type": "revision", "difficulty": "advanced", "topic": topic, "instruction": f"Do a spaced {topic} review to retain mastery."},
        {"type": "challenge", "difficulty": "advanced", "topic": topic, "instruction": f"Complete a challenge that distinguishes {topic} from similar {label}s."},
    ]


def build_adaptive_plan_from_data(
    learner_id: str,
    topics_data: list[dict],
    overall_accuracy_percent: float | None,
    overall_scored_attempts: int,
    activity_days: int = 0,
    time_spent_seconds: float = 0,
) -> dict:
    """Pure core used both by the API and the learner-profile scenario tests.

    topics_data: every letter AND motion sign on the platform, already
    combined by the caller, each shaped as
    {"topic": str, "topic_type": str, "accuracy_percent": float | None,
     "scored_attempts": int, "outcomes": list[bool]}.
    overall_accuracy_percent / overall_scored_attempts: computed across
    ALL topic types combined, so the learner's level reflects everything
    they've practiced, not just letters.
    """
    level = _level(overall_accuracy_percent, overall_scored_attempts)
    topics = []
    for t in topics_data:
        topics.append({
            "topic": t["topic"],
            "topic_type": t["topic_type"],
            "accuracy_percent": t["accuracy_percent"],
            "scored_attempts": t["scored_attempts"],
            "trend": _trend(t.get("outcomes", [])),
        })

    strong = [t for t in topics if t["accuracy_percent"] is not None and t["accuracy_percent"] >= 85 and t["scored_attempts"] >= MIN_EVIDENCE]
    weak = [t for t in topics if t["accuracy_percent"] is not None and t["accuracy_percent"] < 70 and t["scored_attempts"] >= MIN_EVIDENCE]
    more_practice = [t for t in topics if t["scored_attempts"] < MIN_EVIDENCE or (t["accuracy_percent"] is not None and 70 <= t["accuracy_percent"] < 85)]
    strong.sort(key=lambda item: item["accuracy_percent"], reverse=True)
    weak.sort(key=lambda item: item["accuracy_percent"])
    more_practice.sort(key=lambda item: (item["scored_attempts"] >= MIN_EVIDENCE, item["topic_type"], item["topic"]))

    priority_topics = weak + [t for t in more_practice if t not in weak]
    if not priority_topics:
        priority_topics = strong
    recommendations = []
    for index, topic in enumerate(priority_topics[:MAX_TOPICS], start=1):
        accuracy = topic["accuracy_percent"]
        if accuracy is None:
            reason = "No assessment evidence yet — establish a baseline."
        elif accuracy < 70:
            reason = f"Learning gap: {accuracy}% accuracy across {topic['scored_attempts']} scored attempts."
        elif accuracy < 85:
            reason = f"Developing skill: {accuracy}% accuracy; targeted practice can build consistency."
        else:
            reason = f"Mastered at {accuracy}% accuracy; schedule retention practice."
        if topic["trend"] == "declining":
            reason += " Recent results are declining, so it is prioritised."
        elif topic["trend"] == "improving":
            reason += " Recent results are improving."
        recommendations.append({
            "topic": topic["topic"], "topic_type": topic["topic_type"], "priority": index, "reason": reason,
            "activities": _activities(topic["topic"], topic["topic_type"], level, accuracy, topic["trend"]),
        })

    summary = (
        "Start with baseline practice so the plan can adapt to your results."
        if overall_scored_attempts < MIN_EVIDENCE
        else f"Your current adaptive level is {level}; the plan uses your latest accuracy and recent topic trends."
    )
    return {
        "learner_id": learner_id,
        "learning_level": level,
        "profile_summary": summary,
        "overall_accuracy_percent": overall_accuracy_percent,
        "activity_days": activity_days,
        "time_spent_minutes": round(time_spent_seconds / 60, 1),
        "completed_topics": [t["topic"] for t in strong],
        "strong_topics": strong[:5],
        "weak_topics": weak[:5],
        "needs_more_practice": more_practice[:5],
        "recommendations": recommendations,
        "next_assessment": "Complete the recommended activities, then submit three new captures for the top topic. Your next plan will be recalculated from those results.",
    }


def get_adaptive_learning_plan(db: Session, learner_id: str) -> dict:
    analytics = get_learner_analytics(db, learner_id)
    motion_analytics = get_motion_sign_analytics(db, learner_id)

    letter_attempts = (
        db.query(PracticeAttempt)
        .filter(PracticeAttempt.learner_id == learner_id)
        .order_by(PracticeAttempt.created_at.asc())
        .all()
    )
    motion_attempts = (
        db.query(MotionSignAttempt)
        .filter(MotionSignAttempt.learner_id == learner_id)
        .order_by(MotionSignAttempt.created_at.asc())
        .all()
    )

    letter_outcomes: dict[str, list[bool]] = defaultdict(list)
    for row in letter_attempts:
        if row.correct is not None:
            letter_outcomes[row.target_letter].append(bool(row.correct))

    motion_outcomes: dict[str, list[bool]] = defaultdict(list)
    for row in motion_attempts:
        if row.correct is not None:
            motion_outcomes[row.target_sign].append(bool(row.correct))

    topics_data = []
    for letter, stats in analytics["per_letter"].items():
        topics_data.append({
            "topic": letter, "topic_type": "letter",
            "accuracy_percent": stats["accuracy_percent"],
            "scored_attempts": stats["correct"] + stats["incorrect"],
            "outcomes": letter_outcomes.get(letter, []),
        })
    for sign, stats in motion_analytics["per_sign"].items():
        topics_data.append({
            "topic": sign, "topic_type": "motion_sign",
            "accuracy_percent": stats["accuracy_percent"],
            "scored_attempts": stats["correct"] + stats["incorrect"],
            "outcomes": motion_outcomes.get(sign, []),
        })

    combined_scored = analytics["scored_attempts"] + motion_analytics["scored_attempts"]
    combined_correct = analytics["correct_count"] + motion_analytics["correct_count"]
    combined_accuracy = round(combined_correct / combined_scored * 100, 1) if combined_scored else None

    activity_days = len({
        row.created_at.date().isoformat()
        for row in list(letter_attempts) + list(motion_attempts)
        if row.created_at
    })
    time_spent_seconds = sum(
        row.duration_seconds or 0
        for row in db.query(LearningActivity).filter(LearningActivity.learner_id == learner_id).all()
    )

    return build_adaptive_plan_from_data(
        learner_id, topics_data, combined_accuracy, combined_scored, activity_days, time_spent_seconds,
    )
