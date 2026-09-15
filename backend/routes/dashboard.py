"""Learner dashboard routes: KPIs, activity log, demo activity logging."""
from fastapi import APIRouter, Depends

from database import db
from deps import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def get_dashboard(current_user=Depends(get_current_user)):
    profile = db.get_learner_profile(current_user["id"])
    history = db.get_practice_history(current_user["id"], limit=100)

    goals = []
    if profile and profile.get("learning_goals"):
        goals = [g for g in profile["learning_goals"].split(",") if g]

    gesture_stats = db.get_gesture_stats(current_user["id"])

    return {
        "learning_level": profile["learning_level"] if profile else None,
        "preferred_language": profile["preferred_language"] if profile else None,
        "goals": goals,
        "logged_activities_count": len(history),
        "recent_activity": history[:10],
        "has_profile": profile is not None,
        # Milestone 2: real gesture-practice stats, replacing the
        # Milestone-1 placeholder progress chart.
        "gesture_stats": gesture_stats,
    }


@router.post("/log-activity")
def log_activity(current_user=Depends(get_current_user)):
    db.log_practice_activity(current_user["id"], "Practiced ASL alphabet — demo entry")
    return {"message": "Activity logged."}
