"""
Weighted Learning Performance Score — roadmap section 10 ("Performance
Scoring Engine" / "Weighted Scoring Model").

The roadmap defines an exact composite formula:

    Learning Performance Score =
        Gesture Accuracy        (40%) +
        Assessment Performance  (25%) +
        Lesson Completion       (15%) +
        Practice Consistency    (10%) +
        Skill Improvement Rate  (10%)

Every one of these five inputs already exists elsewhere in the app (gesture
accuracy from analytics.py, assessment performance from assessment_reports,
lesson completion from the Course & Content Service, and so on) — this
module's only job is to pull them together into the single weighted number
the roadmap calls for, plus a component breakdown so the dashboard can show
*why* the score is what it is, not just the final number.
"""
from datetime import datetime, timezone, timedelta

from database import db
from intelligence.analytics import compute_analytics, compute_performance_trend

WEIGHTS = {
    "gesture_accuracy": 0.40,
    "assessment_performance": 0.25,
    "lesson_completion": 0.15,
    "practice_consistency": 0.10,
    "skill_improvement_rate": 0.10,
}

CONSISTENCY_WINDOW_DAYS = 14
# Trend slope (accuracy points gained/lost per attempt) beyond which the
# improvement-rate component is fully saturated at 0 or 100.
SLOPE_SATURATION = 2.0


def _gesture_accuracy(analytics: dict) -> float:
    return analytics["overall_accuracy"] if analytics["has_data"] else 0.0


def _assessment_performance(user_id: int, fallback: float) -> float:
    """Most recently generated Assessment Report's overall accuracy. Falls
    back to live gesture accuracy if the learner has never generated one —
    that's a better default than 0, which would unfairly zero out a
    learner's score just for not having clicked 'Generate Report' yet."""
    history = db.get_report_history(user_id, limit=1)
    if history:
        return float(history[0]["overall_accuracy"])
    return fallback


def _lesson_completion(user_id: int) -> float:
    """% of lessons watched across every course the learner is enrolled
    in. 0 if not enrolled in anything yet."""
    enrollments = db.list_my_enrollments(user_id)
    total_lessons = sum(e["lesson_count"] for e in enrollments)
    watched = sum(e["watched_count"] for e in enrollments)
    if total_lessons == 0:
        return 0.0
    return (watched / total_lessons) * 100.0


def _practice_consistency(user_id: int) -> float:
    """% of the last CONSISTENCY_WINDOW_DAYS calendar days that had at
    least one gesture-practice attempt — rewards showing up regularly over
    cramming, same spirit as a streak, without needing a separate streak
    counter to maintain."""
    rows = db.get_all_gesture_attempts(user_id)
    if not rows:
        return 0.0

    cutoff = datetime.now(timezone.utc) - timedelta(days=CONSISTENCY_WINDOW_DAYS)
    practiced_dates = set()
    for r in rows:
        raw = r.get("created_at")
        if not raw:
            continue
        try:
            dt = datetime.fromisoformat(raw.replace(" ", "T"))
        except ValueError:
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt >= cutoff:
            practiced_dates.add(dt.date())

    return min(100.0, (len(practiced_dates) / CONSISTENCY_WINDOW_DAYS) * 100.0)


def _skill_improvement_rate(trend: dict) -> float:
    """Normalizes the linear-regression trend slope from
    compute_performance_trend() onto a 0-100 scale, centered at 50 (flat).
    A learner with fewer than MIN_ATTEMPTS_FOR_TREND attempts has no trend
    yet — default to 50 (neutral) rather than 0, since "not enough data"
    is not the same thing as "getting worse"."""
    fitted = trend.get("trend")
    if not trend.get("has_data") or fitted is None:
        return 50.0
    slope = fitted["slope_per_attempt"]
    capped = max(-SLOPE_SATURATION, min(SLOPE_SATURATION, slope))
    return ((capped + SLOPE_SATURATION) / (2 * SLOPE_SATURATION)) * 100.0


def compute_performance_score(user_id: int) -> dict:
    analytics = compute_analytics(user_id)
    trend = compute_performance_trend(user_id)

    gesture_accuracy = round(_gesture_accuracy(analytics), 1)
    assessment_performance = round(_assessment_performance(user_id, gesture_accuracy), 1)
    lesson_completion = round(_lesson_completion(user_id), 1)
    practice_consistency = round(_practice_consistency(user_id), 1)
    skill_improvement_rate = round(_skill_improvement_rate(trend), 1)

    values = {
        "gesture_accuracy": gesture_accuracy,
        "assessment_performance": assessment_performance,
        "lesson_completion": lesson_completion,
        "practice_consistency": practice_consistency,
        "skill_improvement_rate": skill_improvement_rate,
    }
    score = sum(values[k] * WEIGHTS[k] for k in WEIGHTS)

    return {
        "learning_performance_score": round(score, 1),
        "has_data": analytics["has_data"],
        "components": [
            {
                "key": key,
                "label": label,
                "value": values[key],
                "weight_percent": int(WEIGHTS[key] * 100),
                "contribution": round(values[key] * WEIGHTS[key], 1),
            }
            for key, label in [
                ("gesture_accuracy", "Gesture Accuracy"),
                ("assessment_performance", "Assessment Performance"),
                ("lesson_completion", "Lesson Completion"),
                ("practice_consistency", "Practice Consistency"),
                ("skill_improvement_rate", "Skill Improvement Rate"),
            ]
        ],
    }
