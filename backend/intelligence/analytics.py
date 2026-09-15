"""
Learning Analytics — Milestone 3 (Week 5 & 6, AI Feedback & Learning
Intelligence).

Reads every gesture_attempts row a learner has produced via the Milestone 2
Sign Accuracy Assessment Engine (target gesture, detected gesture, hand-shape
accuracy, position accuracy, overall accuracy, feedback) and turns that raw
attempt history into:

    - overall accuracy / total attempts / best accuracy
    - gesture-wise accuracy (mean, count, min, max)
    - a skill-level classification per gesture:
          < 70%      -> "Needs Improvement"
          70 - 85%   -> "Developing"
          > 85%      -> "Good"
    - weak_areas / strong_areas lists derived from that classification

This is genuinely data-driven: run with zero attempts and you get an empty,
"go practice" response; the numbers change as soon as new attempts are
logged. Everything downstream (feedback.py, recommendations.py,
learning_plan.py) is built on top of this function's output, not on
hard-coded text.
"""
import pandas as pd

from database import db
from gesture.reference_signs import GESTURE_LIBRARY

try:
    from sklearn.linear_model import LinearRegression

    _HAS_SKLEARN = True
except ImportError:  # pragma: no cover - sklearn is a listed dependency
    _HAS_SKLEARN = False

WEAK_THRESHOLD = 70      # < this -> Needs Improvement
DEVELOPING_THRESHOLD = 85  # 70..this -> Developing, > this -> Good
MIN_ATTEMPTS_FOR_TREND = 3
FLAT_SLOPE_THRESHOLD = 0.5  # points-per-attempt; below this we call it "steady"


def _display_name(target_label: str) -> str:
    return GESTURE_LIBRARY.get(target_label, {}).get("display_name", target_label)


def classify_level(avg_accuracy: float) -> str:
    if avg_accuracy < WEAK_THRESHOLD:
        return "Needs Improvement"
    if avg_accuracy <= DEVELOPING_THRESHOLD:
        return "Developing"
    return "Good"


def _empty_analytics() -> dict:
    return {
        "has_data": False,
        "total_attempts": 0,
        "overall_accuracy": 0.0,
        "best_accuracy": 0.0,
        "matched_count": 0,
        "by_gesture": [],
        "weak_areas": [],
        "strong_areas": [],
    }


def compute_analytics(user_id: int) -> dict:
    """
    The single source of truth for Milestone 3: every other intelligence
    module (feedback, recommendations, learning plan) calls this first and
    builds on its output, so there's one consistent picture of the learner.
    """
    rows = db.get_all_gesture_attempts(user_id)
    if not rows:
        return _empty_analytics()

    df = pd.DataFrame(rows)
    df["overall_accuracy"] = df["overall_accuracy"].astype(float)
    df["matched"] = df["matched"].astype(int)

    total_attempts = int(len(df))
    overall_accuracy = round(float(df["overall_accuracy"].mean()), 1)
    best_accuracy = round(float(df["overall_accuracy"].max()), 1)
    matched_count = int(df["matched"].sum())

    grouped = (
        df.groupby("target_label")["overall_accuracy"]
        .agg(["mean", "count", "min", "max"])
        .reset_index()
    )

    by_gesture = []
    for _, r in grouped.iterrows():
        avg = round(float(r["mean"]), 1)
        level = classify_level(avg)
        by_gesture.append(
            {
                "gesture": r["target_label"],
                "display_name": _display_name(r["target_label"]),
                "avg_accuracy": avg,
                "attempts": int(r["count"]),
                "best_accuracy": round(float(r["max"]), 1),
                "worst_accuracy": round(float(r["min"]), 1),
                "level": level,
            }
        )

    # Weakest first — this ordering is reused directly by recommendations
    # and the learning plan so "what to practice first" stays consistent.
    by_gesture.sort(key=lambda g: g["avg_accuracy"])

    weak_areas = [g for g in by_gesture if g["level"] in ("Needs Improvement", "Developing")]
    strong_areas = [g for g in by_gesture if g["level"] == "Good"]

    return {
        "has_data": True,
        "total_attempts": total_attempts,
        "overall_accuracy": overall_accuracy,
        "best_accuracy": best_accuracy,
        "matched_count": matched_count,
        "by_gesture": by_gesture,
        "weak_areas": weak_areas,
        "strong_areas": strong_areas,
    }


def compute_performance_trend(user_id: int) -> dict:
    """
    Learner Performance Dashboard support: the learner's *overall* accuracy
    across every gesture, in chronological order — one point per attempt —
    plus a scikit-learn linear-regression trend fit over the whole series
    (same technique recommendations.py already uses per-gesture, applied
    here across the learner's whole practice history).

    This is what actually turns the dashboard into a *performance* view
    instead of a snapshot: it shows whether the learner is improving over
    time, not just where they stand right now.
    """
    rows = db.get_all_gesture_attempts(user_id)
    if not rows:
        return {"has_data": False, "points": [], "trend": None}

    points = [
        {
            "index": i + 1,
            "gesture": r["target_label"],
            "display_name": _display_name(r["target_label"]),
            "overall_accuracy": float(r["overall_accuracy"]),
            "matched": bool(r["matched"]),
            "created_at": r["created_at"],
        }
        for i, r in enumerate(rows)
    ]

    trend = None
    if _HAS_SKLEARN and len(points) >= MIN_ATTEMPTS_FOR_TREND:
        import numpy as np

        X = np.arange(len(points)).reshape(-1, 1)
        y = np.array([p["overall_accuracy"] for p in points])
        model = LinearRegression().fit(X, y)
        slope = float(model.coef_[0])
        predicted_next = float(model.predict([[len(points)]])[0])
        predicted_next = max(0.0, min(100.0, predicted_next))

        if slope > FLAT_SLOPE_THRESHOLD:
            direction = "improving"
        elif slope < -FLAT_SLOPE_THRESHOLD:
            direction = "declining"
        else:
            direction = "steady"

        trend = {
            "direction": direction,
            "slope_per_attempt": round(slope, 2),
            "predicted_next_accuracy": round(predicted_next, 1),
            "attempts_used": len(points),
        }

    return {"has_data": True, "points": points, "trend": trend}
