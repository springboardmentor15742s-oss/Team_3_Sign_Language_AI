"""
Derives streak, achievement, recent-activity, and performance-forecast
data entirely from real PracticeAttempt history — no mock/placeholder
values. Follows the same null-vs-zero discipline as learning_analytics_
service: a stat with no basis in the data (not enough attempts, no
positive trend, streak of zero) is represented as null/empty/False, never
backfilled with an invented number.
"""

import math
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.practice_attempt import PracticeAttempt

# Accuracy bands used for both the "current level" badge and the forecast.
# Order matters: index into this list is the "band index".
LEVEL_BANDS: list[tuple[float, str]] = [
    (0.0, "Beginner"),
    (50.0, "Elementary"),
    (70.0, "Intermediate"),
    (85.0, "Advanced"),
    (95.0, "Fluent"),
]

STREAK_BADGE_TARGET_DAYS = 3
ALL_LETTERS_BADGE = "alphabet_explorer"
ACCURACY_BADGE_THRESHOLD = 90.0
ACCURACY_BADGE_MIN_SCORED = 20
CENTURY_BADGE_TARGET = 100

# Forecast needs enough real signal before projecting anything.
MIN_SCORED_ATTEMPTS_FOR_FORECAST = 10
MIN_TREND_POINTS_FOR_FORECAST = 3

RECENT_ACTIVITY_LIMIT = 6


def _level_band_index(accuracy: float) -> int:
    band_index = 0
    for i, (threshold, _name) in enumerate(LEVEL_BANDS):
        if accuracy >= threshold:
            band_index = i
    return band_index


def get_current_streak(accuracy_trend: list[dict]) -> int:
    """
    Current consecutive-day practice streak, walking backward from today.
    accuracy_trend (from learning_analytics_service) only contains days
    with at least one real attempt, so every entry here already
    represents a "practiced" day.

    Returns 0 if the learner hasn't practiced today or yesterday — a
    streak that's already lapsed isn't still "current".
    """
    practiced_days = sorted(
        {date.fromisoformat(pt["date"]) for pt in accuracy_trend if pt["date"] != "unknown"}
    )
    if not practiced_days:
        return 0

    today = date.today()
    most_recent = practiced_days[-1]
    if (today - most_recent).days > 1:
        return 0

    streak = 1
    for i in range(len(practiced_days) - 1, 0, -1):
        if (practiced_days[i] - practiced_days[i - 1]).days == 1:
            streak += 1
        else:
            break
    return streak


def get_achievements(analytics: dict, streak: int) -> list[dict]:
    """
    A fixed set of badges, each with a real unlocked/progress state
    computed from analytics (learning_analytics_service.get_learner_analytics
    output) — no badge is ever marked unlocked without the underlying
    numbers to back it.
    """
    total_attempts = analytics["total_attempts"]
    scored_attempts = analytics["scored_attempts"]
    overall_accuracy = analytics["overall_accuracy_percent"]
    total_letters = len(analytics["per_letter"])
    letters_scored = sum(
        1 for stats in analytics["per_letter"].values() if stats["accuracy_percent"] is not None
    )

    return [
        {
            "id": "streak",
            "label": f"{streak}-Day Streak" if streak > 0 else "Build a Streak",
            "description": f"Practice on {STREAK_BADGE_TARGET_DAYS} consecutive days.",
            "unlocked": streak >= STREAK_BADGE_TARGET_DAYS,
            "progress_current": streak,
            "progress_target": STREAK_BADGE_TARGET_DAYS,
        },
        {
            "id": ALL_LETTERS_BADGE,
            "label": "Alphabet Explorer",
            "description": f"Attempt all {total_letters} letters at least once.",
            "unlocked": total_letters > 0 and letters_scored == total_letters,
            "progress_current": letters_scored,
            "progress_target": total_letters,
        },
        {
            "id": "sharp_signer",
            "label": "Sharp Signer",
            "description": f"Reach {ACCURACY_BADGE_THRESHOLD:.0f}% lifetime accuracy (min. {ACCURACY_BADGE_MIN_SCORED} scored attempts).",
            "unlocked": (
                overall_accuracy is not None
                and overall_accuracy >= ACCURACY_BADGE_THRESHOLD
                and scored_attempts >= ACCURACY_BADGE_MIN_SCORED
            ),
            "progress_current": overall_accuracy if overall_accuracy is not None else 0.0,
            "progress_target": ACCURACY_BADGE_THRESHOLD,
        },
        {
            "id": "century_club",
            "label": "Century Club",
            "description": f"Log {CENTURY_BADGE_TARGET} practice attempts.",
            "unlocked": total_attempts >= CENTURY_BADGE_TARGET,
            "progress_current": total_attempts,
            "progress_target": CENTURY_BADGE_TARGET,
        },
    ]


def get_recent_activity(db: Session, learner_id: str, limit: int = RECENT_ACTIVITY_LIMIT) -> list[dict]:
    """
    The learner's most recent logged attempts, newest first. Deliberately
    NOT "lessons" or "assessments completed" — this platform doesn't have
    a course/lesson data model, so the timeline reflects what actually
    happened: real practice attempts, real letters, real outcomes.
    """
    attempts = (
        db.query(PracticeAttempt)
        .filter(PracticeAttempt.learner_id == learner_id)
        .order_by(PracticeAttempt.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {
            "letter": a.target_letter,
            "status": a.status,
            "confidence": a.confidence,
            "created_at": a.created_at,
        }
        for a in attempts
    ]


def get_performance_forecast(analytics: dict) -> dict:
    """
    A real (if simple) linear-trend projection over the learner's actual
    day-by-day accuracy, not a fabricated "success probability". Returns
    available=False with a stated reason when there isn't enough real
    data to project from, rather than showing a number anyway.
    """
    overall_accuracy = analytics["overall_accuracy_percent"]
    scored_attempts = analytics["scored_attempts"]
    accuracy_trend = analytics["accuracy_trend"]

    if overall_accuracy is None or scored_attempts < MIN_SCORED_ATTEMPTS_FOR_FORECAST:
        return {
            "available": False,
            "reason": f"Needs at least {MIN_SCORED_ATTEMPTS_FOR_FORECAST} scored attempts (have {scored_attempts}).",
            "current_level": None,
            "predicted_next_level": None,
            "trend_percent_per_day": None,
            "estimated_days_to_next_level": None,
        }

    band_index = _level_band_index(overall_accuracy)
    current_level = LEVEL_BANDS[band_index][1]
    next_level = LEVEL_BANDS[band_index + 1][1] if band_index + 1 < len(LEVEL_BANDS) else None

    scored_points = [p for p in accuracy_trend if p["accuracy_percent"] is not None]
    trend_slope = None
    if len(scored_points) >= MIN_TREND_POINTS_FOR_FORECAST:
        n = len(scored_points)
        xs = list(range(n))
        ys = [p["accuracy_percent"] for p in scored_points]
        mean_x = sum(xs) / n
        mean_y = sum(ys) / n
        numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
        denominator = sum((x - mean_x) ** 2 for x in xs)
        trend_slope = numerator / denominator if denominator > 0 else 0.0

    estimated_days = None
    if next_level and trend_slope and trend_slope > 0:
        points_needed = LEVEL_BANDS[band_index + 1][0] - overall_accuracy
        if points_needed > 0:
            estimated_days = math.ceil(points_needed / trend_slope)

    return {
        "available": True,
        "reason": None,
        "current_level": current_level,
        "predicted_next_level": next_level,
        "trend_percent_per_day": round(trend_slope, 3) if trend_slope is not None else None,
        "estimated_days_to_next_level": estimated_days,
    }


def get_learner_progress(db: Session, learner_id: str, analytics: dict) -> dict:
    """
    Single entry point bundling streak, achievements, recent activity,
    and forecast — analytics is the already-computed
    learning_analytics_service.get_learner_analytics(...) result, passed
    in rather than recomputed, so callers that need both don't hit the
    PracticeAttempt table twice.
    """
    streak = get_current_streak(analytics["accuracy_trend"])
    return {
        "learner_id": learner_id,
        "current_streak_days": streak,
        "achievements": get_achievements(analytics, streak),
        "recent_activity": get_recent_activity(db, learner_id),
        "forecast": get_performance_forecast(analytics),
    }
