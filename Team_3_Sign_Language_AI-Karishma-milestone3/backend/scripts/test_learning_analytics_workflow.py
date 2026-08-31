"""
Scenario tests for the learning analytics workflow (Task 2 of the
mentor-assigned work): completion rate, frequency patterns,
commonly-missed/avoided topics, and current-vs-previous performance
comparison, against REAL database rows across several distinct learner
profiles — same pattern as test_recommendation_engine_profiles.py and
test_ai_feedback_service.py already established for this codebase.

Creates its own throwaway learners (analyticswf-*@test.com). Run from
backend/:

    venv/bin/python scripts/test_learning_analytics_workflow.py
"""

import sys
import uuid
from datetime import datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.models.practice_attempt import PracticeAttempt
from app.models.motion_sign_attempt import MotionSignAttempt
from app.services.learning_analytics_workflow_service import get_learning_analytics_workflow

LETTERS = ["A", "B", "C", "D"]


def _make_learner(db, email: str, name: str) -> User:
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        db.query(PracticeAttempt).filter(PracticeAttempt.learner_id == existing.id).delete()
        db.query(MotionSignAttempt).filter(MotionSignAttempt.learner_id == existing.id).delete()
        db.commit()
        return existing
    learner = User(id=str(uuid.uuid4()), email=email, name=name, role="learner", hashed_password="test-hash-not-real")
    db.add(learner)
    db.commit()
    db.refresh(learner)
    return learner


def _add_letter_attempts(db, learner_id: str, letter: str, outcomes: list, start: datetime):
    for i, correct in enumerate(outcomes):
        db.add(PracticeAttempt(
            id=str(uuid.uuid4()), learner_id=learner_id, target_letter=letter,
            predicted_letter=letter if correct else "Z", status="pass" if correct else "fail",
            correct=correct, confidence=0.9, created_at=start + timedelta(hours=i),
        ))
    db.commit()


def main():
    db = SessionLocal()
    try:
        # Profile 1: brand-new learner, zero data anywhere — every metric
        # must degrade to an honest "unavailable"/zero, never a fabricated number.
        new_learner = _make_learner(db, "analyticswf-new@test.com", "New Learner")
        wf = get_learning_analytics_workflow(db, new_learner.id)
        print(f"\n=== New learner ({new_learner.email}) ===")
        print(wf)
        assert wf["completion_rate"]["overall_percent"] is not None  # 0/26 letters is a real 0%, not "unavailable"
        assert wf["completion_rate"]["attempted_count"] == 0
        assert wf["frequency_patterns"]["days_active_total"] == 0
        assert wf["frequency_patterns"]["last_active_date"] is None
        assert wf["commonly_missed"] == []
        assert len(wf["avoided_topics"]) == wf["completion_rate"]["total_count"]
        assert wf["performance_comparison"]["available"] is False

        # Profile 2: active learner practicing today, with real hits and
        # misses spread across all 4 letters so completion rate, missed
        # topics, and frequency all have real signal.
        active = _make_learner(db, "analyticswf-active@test.com", "Active Learner")
        # Anchored to noon UTC today (not "now") so the 5-hour spread of
        # attempts below can never cross a calendar-day boundary, however
        # close to midnight this test happens to run.
        today_noon = datetime.combine(datetime.utcnow().date(), time(12, 0))
        _add_letter_attempts(db, active.id, "A", [True, True, False, True, False], today_noon - timedelta(hours=5))
        _add_letter_attempts(db, active.id, "B", [False, False, True], today_noon - timedelta(hours=3))
        _add_letter_attempts(db, active.id, "C", [True], today_noon - timedelta(hours=1))
        # D is never attempted -> should show up in avoided_topics.
        wf = get_learning_analytics_workflow(db, active.id)
        print(f"\n=== Active learner ({active.email}) ===")
        print(wf)
        assert wf["completion_rate"]["attempted_count"] == 3  # A, B, C only
        assert any(t["topic"] == "D" for t in wf["avoided_topics"])
        assert not any(t["topic"] == "A" for t in wf["avoided_topics"])
        assert wf["commonly_missed"][0]["topic"] == "A"  # A has 2 misses, the most of any letter
        assert wf["commonly_missed"][0]["incorrect_count"] == 2
        assert wf["frequency_patterns"]["days_active_total"] == 1
        assert wf["frequency_patterns"]["days_since_last_active"] == 0
        assert wf["frequency_patterns"]["avg_attempts_per_active_day"] == 9.0

        # Profile 3: learner with enough scored attempts in both the
        # current and previous 7-day windows, improving over time -> the
        # comparison should be available with a positive delta.
        improving = _make_learner(db, "analyticswf-improving@test.com", "Improving Learner")
        previous_window_start = today_noon - timedelta(days=10)
        current_window_start = today_noon - timedelta(days=3)
        _add_letter_attempts(db, improving.id, "A", [False, False, False, True], previous_window_start)  # 25% in previous window
        _add_letter_attempts(db, improving.id, "B", [True, True, True, True], current_window_start)  # 100% in current window
        wf = get_learning_analytics_workflow(db, improving.id)
        print(f"\n=== Improving learner ({improving.email}) ===")
        print(wf["performance_comparison"])
        comparison = wf["performance_comparison"]
        assert comparison["available"] is True
        assert comparison["previous_period"]["accuracy_percent"] == 25.0
        assert comparison["current_period"]["accuracy_percent"] == 100.0
        assert comparison["accuracy_delta_percent"] == 75.0
        assert comparison["trend"] == "improving"

        print("\nAll learning analytics workflow scenarios passed: new, active, and improving learners.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
