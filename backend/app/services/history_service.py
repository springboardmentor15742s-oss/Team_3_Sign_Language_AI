"""
Raw, session-by-session practice history — every logged PracticeAttempt
and MotionSignAttempt for a learner, newest first. Unlike
learning_analytics_service's aggregated per-letter/per-day view, this is
the flat log a learner can scroll through session by session (the
"Practice History" page).

Summary numbers (total/scored/accuracy) are read from the SAME
aggregated analytics every other page on this platform already uses
(get_learner_analytics + get_motion_sign_analytics) rather than
recomputed independently here — this page must never disagree with the
dashboard's numbers, matching this codebase's "no parallel source of
truth for accuracy" discipline (see recommendation_service,
learning_analytics_workflow_service).
"""

from datetime import datetime

from sqlalchemy.orm import Session

from app.models.motion_sign_attempt import MotionSignAttempt
from app.models.practice_attempt import PracticeAttempt
from app.services.learning_analytics_service import get_learner_analytics
from app.services.motion_sign_analytics_service import get_motion_sign_analytics

# A generous cap, not real pagination — this project's SQLite dev scale
# doesn't need it, but an unbounded query result isn't a great habit
# even here.
MAX_ENTRIES = 500


def get_practice_history(
    db: Session,
    learner_id: str,
    topic_type: str | None = None,
    status: str | None = None,
) -> dict:
    entries: list[dict] = []

    if topic_type in (None, "letter"):
        letter_attempts = (
            db.query(PracticeAttempt).filter(PracticeAttempt.learner_id == learner_id).all()
        )
        for a in letter_attempts:
            entries.append({
                "id": a.id,
                "topic": a.target_letter,
                "topic_type": "letter",
                "status": a.status,
                "correct": a.correct,
                "confidence": a.confidence,
                "created_at": a.created_at,
            })

    if topic_type in (None, "motion_sign"):
        motion_attempts = (
            db.query(MotionSignAttempt).filter(MotionSignAttempt.learner_id == learner_id).all()
        )
        for a in motion_attempts:
            entries.append({
                "id": a.id,
                "topic": a.target_sign,
                "topic_type": "motion_sign",
                "status": a.status,
                "correct": a.correct,
                "confidence": a.confidence,
                "created_at": a.created_at,
            })

    if status is not None:
        entries = [e for e in entries if e["status"] == status]

    entries.sort(key=lambda e: e["created_at"] or datetime.min, reverse=True)
    entries = entries[:MAX_ENTRIES]

    analytics = get_learner_analytics(db, learner_id)
    motion_analytics = get_motion_sign_analytics(db, learner_id)
    combined_scored = analytics["scored_attempts"] + motion_analytics["scored_attempts"]
    combined_correct = analytics["correct_count"] + motion_analytics["correct_count"]
    combined_total = analytics["total_attempts"] + motion_analytics["total_attempts"]

    return {
        "learner_id": learner_id,
        "total_sessions": combined_total,
        "scored_sessions": combined_scored,
        "accuracy_percent": round(combined_correct / combined_scored * 100, 1) if combined_scored else None,
        "entries": entries,
    }
