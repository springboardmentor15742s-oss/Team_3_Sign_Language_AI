"""
Quick manual check that learning_analytics_service correctly aggregates
a real learner's PracticeAttempt history from the dev DB (the rows saved
by test_feedback_service.py). Run from backend/:

    venv/bin/python scripts/test_learning_analytics.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.services.learning_analytics_service import get_learner_analytics


def main():
    db = SessionLocal()
    try:
        learner = db.query(User).filter(User.email == "lubna@test.com").first()
        if not learner:
            raise RuntimeError("Test learner lubna@test.com not found — run test_feedback_service.py first.")

        analytics = get_learner_analytics(db, learner.id)
        print(f"Analytics for {learner.email} ({learner.id}):\n")
        print(json.dumps(analytics, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
