"""
Quick manual check that recommendation_service builds a sensible
practice queue for a real learner in the dev DB. Run from backend/:

    venv/bin/python scripts/test_recommendations.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.services.recommendation_service import get_recommendations


def main():
    db = SessionLocal()
    try:
        learner = db.query(User).filter(User.email == "lubna@test.com").first()
        if not learner:
            raise RuntimeError("Test learner lubna@test.com not found — run test_feedback_service.py first.")

        result = get_recommendations(db, learner.id)
        print(f"Recommendations for {learner.email} ({learner.id}):\n")
        print(json.dumps(result, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
