"""
Quick manual check that feedback_service generates sensible feedback text
and correctly persists each assessed attempt (pass, fail, and
no_attempt_detected) to the practice_attempts table. Run from backend/:

    venv/bin/python scripts/test_feedback_service.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import Base, SessionLocal, engine
from app.models import practice_attempt  # noqa: F401 — registers the table with Base
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.feedback_service import generate_feedback, save_practice_attempt
from app.services.sign_assessment_service import assess_sign

# (target_letter, gesture_result) — gesture_result mirrors what
# gesture_recognition_service would return; None simulates no hand detected.
SIMULATED_ATTEMPTS = [
    ("A", {"letter": "A", "confidence": 0.95}),  # pass
    ("A", {"letter": "B", "confidence": 0.61}),  # fail
    ("L", None),  # no_attempt_detected
    ("F", {"letter": "F", "confidence": 0.74}),  # pass
]


def get_or_create_test_learner(db) -> User:
    learner = db.query(User).filter(User.role == "learner").first()
    if learner:
        return learner

    learner = User(
        id="test-learner",
        name="Test Learner",
        email="test-learner@example.com",
        hashed_password=hash_password("test-password"),
        role="learner",
    )
    db.add(learner)
    db.commit()
    db.refresh(learner)
    return learner


def main():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        learner = get_or_create_test_learner(db)
        print(f"Using learner: {learner.email} ({learner.id})\n")

        for target_letter, gesture_result in SIMULATED_ATTEMPTS:
            assessment = assess_sign(gesture_result, target_letter)
            feedback = generate_feedback(assessment)
            saved = save_practice_attempt(db, learner.id, assessment)

            print(f"Target: {target_letter}")
            print(f"  Assessment: {assessment}")
            print(f"  Feedback:   {feedback}")
            print(f"  Saved row:  id={saved.id} status={saved.status} created_at={saved.created_at}\n")

        total_saved = db.query(practice_attempt.PracticeAttempt).filter(
            practice_attempt.PracticeAttempt.learner_id == learner.id
        ).count()
        print(f"Total practice_attempts rows for this learner: {total_saved}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
