"""
AI Feedback & Learning Intelligence routes — Milestone 3.

Implements the roadmap's Milestone 3 flow end to end:

    Milestone 2 Assessment Results -> Store Results -> Learning Analytics ->
    Find Weak Areas -> Feedback Engine -> Recommendation Engine ->
    Personalized Learning Plan -> Learner Dashboard

Every endpoint here is derived live from the calling learner's own
gesture_attempts rows (via intelligence/analytics.py) — nothing is
hard-coded per user.
"""
from fastapi import APIRouter, Depends
from fastapi.responses import PlainTextResponse

from database import db
from deps import get_current_user
from intelligence.analytics import compute_analytics, compute_performance_trend
from intelligence.feedback import generate_feedback
from intelligence.learning_plan import build_learning_plan
from intelligence.recommendations import generate_recommendations
from intelligence.report import build_assessment_report, render_report_text
from intelligence.score import compute_performance_score

router = APIRouter(prefix="/api/intelligence", tags=["intelligence"])


def _build_report_for(current_user):
    """Shared helper: assemble the full Milestone-3 pipeline for one user."""
    a = compute_analytics(current_user["id"])
    fb = generate_feedback(a, current_user["id"])
    recs = generate_recommendations(a, current_user["id"])
    plan = build_learning_plan(recs)
    profile = db.get_learner_profile(current_user["id"])
    return build_assessment_report(current_user, profile, a, fb, recs, plan)


@router.get("/analytics")
def analytics(current_user=Depends(get_current_user)):
    """Learning Analytics: overall accuracy, per-gesture accuracy, skill levels."""
    return compute_analytics(current_user["id"])


@router.get("/weak-areas")
def weak_areas(current_user=Depends(get_current_user)):
    """Weak-area identification, split from analytics for a focused widget."""
    a = compute_analytics(current_user["id"])
    return {"weak_areas": a["weak_areas"], "strong_areas": a["strong_areas"]}


@router.get("/feedback")
def feedback(current_user=Depends(get_current_user)):
    """AI Feedback & Correction Engine — cross-attempt feedback, not per-attempt."""
    a = compute_analytics(current_user["id"])
    return generate_feedback(a, current_user["id"])


@router.get("/recommendations")
def recommendations(current_user=Depends(get_current_user)):
    """Recommendation Engine — practice counts + trend/forecast per weak gesture."""
    a = compute_analytics(current_user["id"])
    return {"recommendations": generate_recommendations(a, current_user["id"])}


@router.get("/learning-plan")
def learning_plan(current_user=Depends(get_current_user)):
    """Personalized Learning Plan — today's ordered practice plan."""
    a = compute_analytics(current_user["id"])
    recs = generate_recommendations(a, current_user["id"])
    return build_learning_plan(recs)


@router.get("/performance-trend")
def performance_trend(current_user=Depends(get_current_user)):
    """Learner Performance Dashboard — overall accuracy over time + trend/forecast."""
    return compute_performance_trend(current_user["id"])


@router.get("/performance-score")
def performance_score(current_user=Depends(get_current_user)):
    """Weighted Learning Performance Score (roadmap section 10): Gesture
    Accuracy 40% + Assessment Performance 25% + Lesson Completion 15% +
    Practice Consistency 10% + Skill Improvement Rate 10%, combined into a
    single 0-100 composite score with a component-level breakdown."""
    return compute_performance_score(current_user["id"])


@router.get("/summary")
def summary(current_user=Depends(get_current_user)):
    """
    Convenience endpoint bundling analytics + feedback + recommendations +
    learning plan + performance trend in one call, so the Learner
    Performance Dashboard can render its whole Milestone 3 section with a
    single request instead of five.
    """
    a = compute_analytics(current_user["id"])
    fb = generate_feedback(a, current_user["id"])
    recs = generate_recommendations(a, current_user["id"])
    plan = build_learning_plan(recs)
    trend = compute_performance_trend(current_user["id"])
    score = compute_performance_score(current_user["id"])
    return {
        "analytics": a,
        "feedback": fb,
        "recommendations": recs,
        "learning_plan": plan,
        "performance_trend": trend,
        "performance_score": score,
    }


@router.get("/report")
def assessment_report(current_user=Depends(get_current_user)):
    """
    Generate Assessment Reports — assembles analytics, AI feedback,
    recommendations, and the learning plan into one dated report and logs
    the generation event to `assessment_reports` (so report history is
    available for the learner/instructor dashboards).
    """
    report = _build_report_for(current_user)
    ov = report["overview"]
    db.log_assessment_report(
        current_user["id"],
        ov["total_attempts"],
        ov["overall_accuracy"],
        len(report["weaknesses"]),
        len(report["strengths"]),
    )
    return report


@router.get("/report/download")
def download_assessment_report(current_user=Depends(get_current_user)):
    """Same report as /report, rendered as a downloadable plain-text file."""
    report = _build_report_for(current_user)
    text = render_report_text(report)
    filename = f"{report['report_id']}.txt"
    return PlainTextResponse(
        content=text,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/report/history")
def report_history(current_user=Depends(get_current_user)):
    """Past report-generation events for this learner, most recent first."""
    return {"reports": db.get_report_history(current_user["id"])}
