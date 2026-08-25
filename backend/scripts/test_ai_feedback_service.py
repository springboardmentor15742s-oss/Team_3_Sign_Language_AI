"""
Scenario tests for the AI feedback engine (ai_feedback_service) — Task 1
of the mentor-assigned work. Exercises both layers against REAL database
rows across several distinct learner profiles/performance levels (new,
struggling/beginner, strong/advanced, intermediate/mixed), and tests
generate_activity_feedback() individually against sample assessment
responses at each tier, the same pattern
test_recommendation_engine_profiles.py already established for this
codebase.

Creates its own throwaway learners (aifeedback-*@test.com) so this can be
re-run repeatedly without depending on / disturbing other scripts' seed
data. Run from backend/:

    venv/bin/python scripts/test_ai_feedback_service.py
"""

import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.models.practice_attempt import PracticeAttempt
from app.models.motion_sign_attempt import MotionSignAttempt
from app.services.ai_feedback_service import generate_activity_feedback, get_learner_feedback

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


def _add_letter_attempts(db, learner_id: str, letter: str, outcomes: list, start: datetime, predicted_when_wrong: str = "X"):
    for i, correct in enumerate(outcomes):
        db.add(PracticeAttempt(
            id=str(uuid.uuid4()), learner_id=learner_id, target_letter=letter,
            predicted_letter=letter if correct else predicted_when_wrong,
            status="pass" if correct else "fail", correct=correct, confidence=0.9,
            created_at=start + timedelta(hours=i),
        ))
    db.commit()


def main():
    db = SessionLocal()
    start = datetime(2026, 1, 1)
    try:
        # --- Layer 2: aggregate feedback across distinct learner profiles ---

        # Profile 1: brand-new learner, zero attempts.
        new_learner = _make_learner(db, "aifeedback-new@test.com", "New Learner")
        fb = get_learner_feedback(db, new_learner.id)
        print(f"\n=== New learner ({new_learner.email}) ===")
        print(fb)
        assert fb["learner_level"] == "beginner"
        assert fb["performance"]["overall_accuracy_percent"] is None
        assert "No scored attempts yet" in fb["performance"]["summary"]
        assert fb["errors"] == []

        # Profile 2: struggling learner -> beginner tier. Same letter
        # mistaken for the same wrong letter repeatedly so a confusion
        # pair also exists, to prove it's withheld at beginner tier.
        weak = _make_learner(db, "aifeedback-weak@test.com", "Struggling Learner")
        for letter in LETTERS:
            _add_letter_attempts(db, weak.id, letter, [False] * 7 + [True] * 3, start, predicted_when_wrong="Z")
        fb = get_learner_feedback(db, weak.id)
        print(f"\n=== Struggling learner ({weak.email}) ===")
        print(fb)
        assert fb["learner_level"] == "beginner"
        assert fb["errors"], "a struggling learner should have concrete error entries"
        assert all("detail" in e for e in fb["errors"])
        # The core Task-1 requirement: a beginner never gets the
        # confusion-pair master-level diagnostic.
        assert not any(e["accuracy_percent"] is None and e["scored_attempts"] is None for e in fb["errors"]), (
            "a beginner-tier feedback report leaked a confusion-pair (master-level) error entry"
        )
        assert fb["areas_for_improvement"], "a struggling learner should have improvement areas with suggested activities"
        assert all(a["suggested_activities"] for a in fb["areas_for_improvement"])

        # Profile 3: strong learner -> advanced tier.
        strong = _make_learner(db, "aifeedback-strong@test.com", "Strong Learner")
        for letter in LETTERS:
            _add_letter_attempts(db, strong.id, letter, [True] * 9 + [False], start, predicted_when_wrong="Z")
        fb = get_learner_feedback(db, strong.id)
        print(f"\n=== Strong learner ({strong.email}) ===")
        print(fb)
        assert fb["learner_level"] == "advanced"
        assert fb["performance"]["summary"] == (
            "Your accuracy is strong overall. What's left is fine-tuning the few remaining weak spots."
        )

        # Profile 4: intermediate/mixed learner — confusion pairs ARE
        # allowed to surface once past beginner tier.
        mixed = _make_learner(db, "aifeedback-mixed@test.com", "Mixed Learner")
        for letter in LETTERS:
            _add_letter_attempts(db, mixed.id, letter, [True] * 7 + [False] * 3, start, predicted_when_wrong="Q")
        fb = get_learner_feedback(db, mixed.id)
        print(f"\n=== Mixed/intermediate learner ({mixed.email}) ===")
        print(fb)
        assert fb["learner_level"] in ("intermediate", "advanced")
        if fb["learner_level"] != "beginner":
            confusion_entries = [e for e in fb["errors"] if e["accuracy_percent"] is None]
            assert confusion_entries, "an intermediate/advanced learner with real confusion pairs should see them"

        # --- Layer 1: per-activity feedback tested individually, across
        # every tier and outcome ---
        print("\n=== Per-activity feedback (sample learner responses) ===")
        sample_results = [
            {"target_letter": "A", "status": "pass", "correct": True, "confidence": 0.95},
            {"target_letter": "B", "status": "fail", "correct": False, "confidence": 0.4},
            {"target_letter": "L", "status": "no_attempt_detected", "correct": None, "confidence": None},
        ]
        for level in ("beginner", "intermediate", "advanced"):
            for result in sample_results:
                out = generate_activity_feedback(result, level)
                print(f"[{level:12s}] {result['status']:18s} -> {out}")
                assert out["learner_level"] == level
                assert out["topic"] == result["target_letter"]
                assert out["message"]
                if result["status"] == "pass":
                    assert out["error"] is None and out["improvement_tip"] is None
                else:
                    assert out["error"] and out["improvement_tip"], "fail/no_attempt should always include error + improvement_tip"

        # Beginner phrasing must never contain the more clinical
        # intermediate/advanced language for the same failed attempt —
        # the literal "no master-level feedback for a beginner" check.
        beginner_fail = generate_activity_feedback(sample_results[1], "beginner")
        advanced_fail = generate_activity_feedback(sample_results[1], "advanced")
        assert beginner_fail["error"] != advanced_fail["error"]
        assert "normal" in beginner_fail["performance"].lower()

        print("\nAll AI feedback engine scenarios passed: new, struggling, strong, and mixed learners; all tiers x all outcomes.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
