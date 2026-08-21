"""
End-to-end scenario tests for the recommendation engine (recommendation_service
+ adaptive_learning_service) against REAL database rows across several distinct
learner profiles and performance levels — not just one test learner, and not
just letters: each profile also gets motion-sign (Wave/Clap) attempts so the
combined-topic logic added in this pass is actually exercised.

Creates its own throwaway learners (recengine-*@test.com) and attempt rows
directly rather than reusing the shared dev-DB test learners, so this can be
re-run repeatedly without depending on / disturbing other scripts' seed data.
Run from backend/:

    venv/bin/python scripts/test_recommendation_engine_profiles.py
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
from app.services.recommendation_service import get_recommendations
from app.services.adaptive_learning_service import get_adaptive_learning_plan

LETTERS_A_D = ["A", "B", "C", "D"]
MOTION_SIGNS = ["Wave", "Clap"]


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
            predicted_letter=letter if correct else "X", status="pass" if correct else "fail",
            correct=correct, confidence=0.9, created_at=start + timedelta(hours=i),
        ))
    db.commit()


def _add_motion_attempts(db, learner_id: str, sign: str, outcomes: list, start: datetime):
    other_sign = "Clap" if sign == "Wave" else "Wave"
    for i, correct in enumerate(outcomes):
        db.add(MotionSignAttempt(
            id=str(uuid.uuid4()), learner_id=learner_id, target_sign=sign,
            predicted_sign=sign if correct else other_sign, status="pass" if correct else "fail",
            correct=correct, confidence=None, frame_count=20, created_at=start + timedelta(hours=i),
        ))
    db.commit()


def _report(db, learner: User, label: str):
    recs = get_recommendations(db, learner.id)
    plan = get_adaptive_learning_plan(db, learner.id)
    print(f"\n=== {label} ({learner.email}) ===")
    print(f"level: {plan['learning_level']}  overall_accuracy: {plan['overall_accuracy_percent']}")
    print("recommendations (mixed queue):")
    for r in recs["recommendations"]:
        print(f"  [{r['topic_type']:11s}] {r['topic']:6s} - {r['reason']}")
    print("adaptive plan top topics:")
    for rec in plan["recommendations"]:
        print(f"  #{rec['priority']} [{rec['topic_type']}] {rec['topic']} - {rec['reason']}")
    return recs, plan


def main():
    db = SessionLocal()
    start = datetime(2026, 1, 1)
    try:
        # Profile 1: brand new learner, zero attempts anywhere.
        new_learner = _make_learner(db, "recengine-new@test.com", "New Learner")
        recs, plan = _report(db, new_learner, "Brand-new learner (no data)")
        assert plan["learning_level"] == "beginner"
        assert recs["recommendations"], "a brand-new learner should still get 'not yet practiced' recommendations"
        assert all(r["reason"] == "not yet practiced" for r in recs["recommendations"])

        # Profile 2: strong across both topic types.
        strong = _make_learner(db, "recengine-strong@test.com", "Strong Learner")
        for letter in LETTERS_A_D:
            _add_letter_attempts(db, strong.id, letter, [True] * 9 + [False], start)
        for sign in MOTION_SIGNS:
            _add_motion_attempts(db, strong.id, sign, [True] * 9 + [False], start)
        recs, plan = _report(db, strong, "Strong learner (letters + motion signs)")
        assert plan["learning_level"] == "advanced"
        assert set(plan["completed_topics"]) >= {"A", "B", "C", "D", "Wave", "Clap"}

        # Profile 3: struggling across both topic types.
        weak = _make_learner(db, "recengine-weak@test.com", "Struggling Learner")
        for letter in LETTERS_A_D:
            _add_letter_attempts(db, weak.id, letter, [False] * 7 + [True] * 3, start)
        for sign in MOTION_SIGNS:
            _add_motion_attempts(db, weak.id, sign, [False] * 7 + [True] * 3, start)
        recs, plan = _report(db, weak, "Struggling learner (letters + motion signs)")
        assert plan["learning_level"] == "beginner"
        assert recs["recommendations"][0]["reason"].startswith("weak area")

        # Profile 4: mixed - strong at letters, weak at motion signs. This is
        # the case that specifically exercises combined-topic reasoning: a
        # learner whose per-topic-type engines would disagree if run apart.
        mixed = _make_learner(db, "recengine-mixed@test.com", "Mixed Learner")
        for letter in LETTERS_A_D:
            _add_letter_attempts(db, mixed.id, letter, [True] * 9 + [False], start)
        _add_motion_attempts(db, mixed.id, "Wave", [False] * 8 + [True] * 2, start)
        _add_motion_attempts(db, mixed.id, "Clap", [True] * 5, start)
        recs, plan = _report(db, mixed, "Mixed learner (strong letters, weak Wave)")
        top = recs["recommendations"][0]
        assert top["topic"] == "Wave" and top["topic_type"] == "motion_sign", (
            f"expected Wave to surface first for a learner who is strong everywhere except it, got {top}"
        )

        # Profile 5: same mixed learner, but filtered to letters only - the
        # guard Practice.tsx relies on so it never gets handed a motion sign.
        letter_only = get_recommendations(db, mixed.id, topic_type="letter")
        assert all(r["topic_type"] == "letter" for r in letter_only["recommendations"]), (
            "topic_type='letter' filter leaked a non-letter recommendation"
        )

        print("\nAll recommendation-engine profile scenarios passed: new, strong, struggling, and mixed learners.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
