"""
Quick manual check that recommendation_service builds a sensible
practice queue for a real learner. Run from backend/:

    venv/bin/python scripts/test_recommendations.py
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.user import User
from app.services.auth_service import hash_password
from app.services.recommendation_service import get_recommendations


def get_or_create_test_learner(db) -> User:
    # See test_learning_analytics.py's own copy of this helper for why:
    # "lubna@test.com" was previously assumed to already exist rather
    # than created by any script.
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

        result = get_recommendations(db, learner.id)
        print(f"Recommendations for {learner.email} ({learner.id}):\n")
        print(json.dumps(result, indent=2))
    finally:
        db.close()


if __name__ == "__main__":
    main()
