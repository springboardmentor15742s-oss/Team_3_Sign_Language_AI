"""
Recommendation Engine — Milestone 3.

Turns analytics.compute_analytics()'s weak_areas / strong_areas into
concrete, personalized practice recommendations:

    Needs Improvement (<70%)  -> practice 5 attempts
    Developing (70-85%)       -> practice 3 attempts
    Good (>85%), maintenance  -> practice 2 attempts (keeps the skill sharp)

Per the roadmap's tooling table ("AI/ML: Scikit-learn ... later, make the
recommendation model more advanced using Scikit-learn"), each weak gesture
also gets a lightweight trend/forecast: a linear regression fit over that
gesture's attempt-by-attempt accuracy, predicting whether the learner is
improving, declining, or steady, and what their next-attempt accuracy is
likely to be. This directly covers the roadmap's "performance forecasting"
requirement. It only activates once there's enough data (>= 3 attempts on
that gesture) and degrades gracefully to `None` otherwise — no fabricated
numbers from thin data.
"""
import numpy as np

from database import db

try:
    from sklearn.linear_model import LinearRegression

    _HAS_SKLEARN = True
except ImportError:  # pragma: no cover - sklearn is a listed dependency
    _HAS_SKLEARN = False

MIN_ATTEMPTS_FOR_TREND = 3
FLAT_SLOPE_THRESHOLD = 0.5  # points-per-attempt; below this we call it "steady"

_PRACTICE_COUNT_BY_LEVEL = {
    "Needs Improvement": 5,
    "Developing": 3,
}
MAINTENANCE_PRACTICE_COUNT = 2


def _trend_for_gesture(user_id: int, target_label: str):
    """
    Performance forecasting: fits accuracy-over-attempt-index with a simple
    linear regression (scikit-learn) for one gesture and returns the trend
    direction + a predicted next-attempt accuracy. Returns None when there
    isn't enough history yet to fit a meaningful line.
    """
    if not _HAS_SKLEARN:
        return None

    rows = [r for r in db.get_all_gesture_attempts(user_id) if r["target_label"] == target_label]
    if len(rows) < MIN_ATTEMPTS_FOR_TREND:
        return None

    X = np.arange(len(rows)).reshape(-1, 1)
    y = np.array([float(r["overall_accuracy"]) for r in rows])

    model = LinearRegression().fit(X, y)
    slope = float(model.coef_[0])
    predicted_next = float(model.predict([[len(rows)]])[0])
    predicted_next = max(0.0, min(100.0, predicted_next))

    if slope > FLAT_SLOPE_THRESHOLD:
        direction = "improving"
    elif slope < -FLAT_SLOPE_THRESHOLD:
        direction = "declining"
    else:
        direction = "steady"

    return {
        "direction": direction,
        "slope_per_attempt": round(slope, 2),
        "predicted_next_accuracy": round(predicted_next, 1),
        "attempts_used": len(rows),
    }


def generate_recommendations(analytics: dict, user_id: int) -> list:
    """
    Returns a list of recommendation dicts, weakest gesture first:
        {
            "gesture": "PEACE",
            "display_name": "Peace / Victory Sign",
            "avg_accuracy": 60.0,
            "level": "Needs Improvement",
            "practice_count": 5,
            "reason": "Average accuracy 60.0% — needs improvement.",
            "trend": {...} | None,
        }
    """
    if not analytics["has_data"]:
        return []

    recommendations = []
    for g in analytics["weak_areas"]:
        practice_count = _PRACTICE_COUNT_BY_LEVEL.get(g["level"], MAINTENANCE_PRACTICE_COUNT)
        trend = _trend_for_gesture(user_id, g["gesture"])
        reason = f"Average accuracy {g['avg_accuracy']}% — {g['level'].lower()}."
        if trend and trend["direction"] == "declining":
            reason += " Recent attempts are trending down — prioritize this one."
        elif trend and trend["direction"] == "improving":
            reason += " You're trending upward here — a few more reps should get you over the line."
        recommendations.append(
            {
                "gesture": g["gesture"],
                "display_name": g["display_name"],
                "avg_accuracy": g["avg_accuracy"],
                "level": g["level"],
                "practice_count": practice_count,
                "reason": reason,
                "trend": trend,
            }
        )

    # Maintenance recommendation: light practice on the learner's strongest
    # gesture so it doesn't get neglected once it's "done".
    if analytics["strong_areas"]:
        best = max(analytics["strong_areas"], key=lambda g: g["avg_accuracy"])
        recommendations.append(
            {
                "gesture": best["gesture"],
                "display_name": best["display_name"],
                "avg_accuracy": best["avg_accuracy"],
                "level": best["level"],
                "practice_count": MAINTENANCE_PRACTICE_COUNT,
                "reason": "Already strong — a little maintenance practice keeps it sharp.",
                "trend": _trend_for_gesture(user_id, best["gesture"]),
            }
        )

    return recommendations
