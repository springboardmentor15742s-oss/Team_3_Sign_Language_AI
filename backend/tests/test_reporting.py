"""
Covers the reporting module (app/routers/instructor.py's /reports/*
endpoints, app/services/reporting_service.py, reporting_pdf_service.py):
class/roster PDF export, the assignment/completion report (JSON + PDF),
and that instructor-roster vs. admin-platform scoping never disagrees
with who's actually on a roster.
"""

import pytest


@pytest.fixture()
def roster(make_user, db_session):
    """One instructor with one learner on their roster, and an
    unaffiliated second instructor to exercise roster-scoping denials."""
    from app.services.instructor_service import add_learner_to_roster_by_id
    from app.models.instructor_learner import InstructorLearner
    from app.models.instructor_assignment import InstructorAssignment

    instructor = make_user("Report Instructor", "rpt-instructor@test.com", "instructor")
    instructor2 = make_user("Report Instructor Two", "rpt-instructor-2@test.com", "instructor")
    admin = make_user("Report Admin", "rpt-admin@test.com", "admin")
    learner = make_user("Report Learner", "rpt-learner@test.com", "learner")

    db_session.query(InstructorAssignment).filter(InstructorAssignment.learner_id == learner.id).delete()
    db_session.query(InstructorLearner).filter(
        InstructorLearner.instructor_id.in_([instructor.id, instructor2.id])
    ).delete(synchronize_session=False)
    db_session.commit()
    add_learner_to_roster_by_id(db_session, instructor_id=instructor.id, learner_id=learner.id)

    return {"instructor": instructor, "instructor2": instructor2, "admin": admin, "learner": learner}


@pytest.fixture()
def assignments(client, roster, auth_headers):
    """One overdue, one open assignment for the roster learner."""
    instructor_headers = auth_headers(roster["instructor"])
    learner_id = roster["learner"].id

    r = client.post(
        f"/api/instructor/learners/{learner_id}/assignments",
        data={"topic": "A", "topic_type": "letter", "due_date": "2020-01-01"},
        headers=instructor_headers,
    )
    assert r.status_code == 200
    r = client.post(
        f"/api/instructor/learners/{learner_id}/assignments",
        data={"topic": "B", "topic_type": "letter"},
        headers=instructor_headers,
    )
    assert r.status_code == 200


def test_class_report_pdf_scopes_by_role(client, roster, auth_headers):
    instructor_headers = auth_headers(roster["instructor"])
    admin_headers = auth_headers(roster["admin"])
    learner_headers = auth_headers(roster["learner"])

    r = client.get("/api/instructor/reports/class/pdf", headers=instructor_headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert "roster-report" in r.headers["content-disposition"]
    assert len(r.content) > 500

    r = client.get("/api/instructor/reports/class/pdf", headers=admin_headers)
    assert r.status_code == 200
    assert "platform-report" in r.headers["content-disposition"]

    r = client.get("/api/instructor/reports/class/pdf", headers=learner_headers)
    assert r.status_code == 403


def test_assignment_report_json_and_scoping(client, roster, assignments, auth_headers):
    instructor_headers = auth_headers(roster["instructor"])
    admin_headers = auth_headers(roster["admin"])
    learner_headers = auth_headers(roster["learner"])

    r = client.get("/api/instructor/reports/assignments", headers=instructor_headers)
    assert r.status_code == 200
    body = r.json()
    assert body["scope"] == "roster"
    assert body["total_count"] == 2
    assert body["overdue_count"] == 1
    overdue_rows = [row for row in body["rows"] if row["overdue"]]
    assert len(overdue_rows) == 1
    assert overdue_rows[0]["completed"] is False

    r = client.get("/api/instructor/reports/assignments", headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["scope"] == "platform"
    assert r.json()["total_count"] >= body["total_count"]

    r = client.get("/api/instructor/reports/assignments", headers=learner_headers)
    assert r.status_code == 403


def test_assignment_report_pdf(client, roster, assignments, auth_headers):
    r = client.get("/api/instructor/reports/assignments/pdf", headers=auth_headers(roster["instructor"]))
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert "roster-assignment-report" in r.headers["content-disposition"]
    assert len(r.content) > 500


def test_empty_roster_does_not_crash(client, roster, auth_headers):
    instructor2_headers = auth_headers(roster["instructor2"])

    r = client.get("/api/instructor/reports/class/pdf", headers=instructor2_headers)
    assert r.status_code == 200

    r = client.get("/api/instructor/reports/assignments", headers=instructor2_headers)
    assert r.status_code == 200
    assert r.json()["total_count"] == 0
