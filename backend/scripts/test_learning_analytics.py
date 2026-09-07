"""
Quick manual check that learning_analytics_service correctly aggregates
a real learner's PracticeAttempt history. Run from backend/:

    venv/bin/python scripts/test_learning_analytics.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.learning_analytics_service import get_learner_analytics


def get_or_create_test_learner(db) -> User:
    # Previously assumed "lubna@test.com" already existed in whatever DB
    # this ran against (created by hand at some point, outside any
    # script) — that's real hidden state, not something this script
    # could ever recreate on a fresh database. Same get-or-create-by-
    # email pattern as test_feedback_service.py's own test learner, so
    # this script is actually self-contained.
    learner = db.query(User).filter(User.email == "lubna@test.com").first()
    if learner is None:
        learner = User(
            id="test-learner-lubna", name="Lubna (Test)", email="lubna@test.com",
            hashed_password=hash_password("test-password"), role="learner",
        )
        db.add(learner)
        db.commit()
        db.refresh(learner)
    return learner


def main():
    db = SessionLocal()
    try:
        learner = get_or_create_test_learner(db)

        analytics = get_learner_analytics(db, learner.id)
        print(f"Analytics for {learner.email} ({learner.id}):\n")
        print(json.dumps(analytics, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
