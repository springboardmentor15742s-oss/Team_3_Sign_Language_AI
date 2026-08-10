"""
Quick manual check that learning_plan_service builds a sensible
personalized practice plan for a real learner in the dev DB. Run from
backend/:

    venv/bin/python scripts/test_learning_plan.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.services.learning_plan_service import generate_learning_plan


def main():
    db = SessionLocal()
    try:
        learner = db.query(User).filter(User.email == "lubna@test.com").first()
        if not learner:
            raise RuntimeError("Test learner lubna@test.com not found — run test_feedback_service.py first.")

        plan = generate_learning_plan(db, learner.id)
        print(f"Learning plan for {learner.email} ({learner.id}):\n")
        print(json.dumps(plan, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
