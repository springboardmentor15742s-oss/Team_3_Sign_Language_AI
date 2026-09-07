"""
Covers app/services/class_trends_service.py: roster-wide accuracy
aggregated by day (weighted by real attempt counts, not a naive average
of per-learner percentages) and the course-completion breakdown.
"""

import uuid
from datetime import datetime, timedelta

import pytest


@pytest.fixture()
def roster_with_attempts(make_user, db_session):
    from app.models.instructor_learner import InstructorLearner
    from app.models.practice_attempt import PracticeAttempt
    from app.services.instructor_service import add_learner_to_roster_by_id

    instructor = make_user("Trend Instructor", "trend-instructor@test.com", "instructor")
    admin = make_user("Trend Admin", "trend-admin@test.com", "admin")
    learner = make_user("Trend Learner", "trend-learner@test.com", "learner")

    db_session.query(PracticeAttempt).filter(PracticeAttempt.learner_id == learner.id).delete()
    db_session.query(InstructorLearner).filter(InstructorLearner.instructor_id == instructor.id).delete()
    db_session.commit()
    add_learner_to_roster_by_id(db_session, instructor_id=instructor.id, learner_id=learner.id)

    yesterday = datetime.utcnow() - timedelta(days=1)
    for letter, correct, created_at in [("A", True, yesterday), ("B", False, yesterday), ("A", True, datetime.utcnow())]:
        db_session.add(PracticeAttempt(
            id=str(uuid.uuid4()), learner_id=learner.id, target_letter=letter,
            predicted_letter=letter if correct else "X", status="pass" if correct else "fail",
            correct=correct, confidence=0.9, created_at=created_at,
        ))
    db_session.commit()

    return {"instructor": instructor, "admin": admin, "learner": learner}


def test_accuracy_trend_is_weighted_by_real_attempts(client, roster_with_attempts, auth_headers):
    r = client.get("/api/instructor/class-trends", headers=auth_headers(roster_with_attempts["instructor"]))
    assert r.status_code == 200
    body = r.json()

    assert len(body["accuracy_trend"]) == 2
    total_scored = sum(p["scored_attempts"] for p in body["accuracy_trend"])
    assert total_scored == 3

    day_with_two = next(p for p in body["accuracy_trend"] if p["scored_attempts"] == 2)
    assert day_with_two["accuracy_percent"] == 50.0  # 1 correct of 2, not an average of two 100%/0% days


def test_course_completion_breakdown_and_admin_scope(client, roster_with_attempts, auth_headers):
    r = client.get("/api/instructor/class-trends", headers=auth_headers(roster_with_attempts["instructor"]))
    course_completion = {c["course_id"]: c for c in r.json()["course_completion"]}
    assert len(course_completion) == 3
    assert course_completion["alphabet-fundamentals"]["learner_count"] == 1
    assert course_completion["alphabet-fundamentals"]["certified_count"] is not None

    instructor_scored = sum(p["scored_attempts"] for p in r.json()["accuracy_trend"])

    r = client.get("/api/instructor/class-trends", headers=auth_headers(roster_with_attempts["admin"]))
    assert r.status_code == 200
    admin_scored = sum(p["scored_attempts"] for p in r.json()["accuracy_trend"])
    assert admin_scored >= instructor_scored
