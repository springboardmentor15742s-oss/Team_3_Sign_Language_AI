"""
Covers the input-validation gaps found and closed during the backend
hardening pass: unbounded free-text fields (assignment notes, instructor
notes, certificate revoke reasons) and password strength on self-service
registration. Each of these previously accepted anything a client sent —
these tests pin down both the new rejection and that legitimate,
reasonably-sized input still works.
"""

import pytest

from app.schemas.certificate import MAX_REVOKE_REASON_LENGTH
from app.schemas.instructor_note import MAX_NOTE_LENGTH
from app.schemas.user import MAX_NAME_LENGTH, MIN_PASSWORD_LENGTH
from app.services.instructor_assignment_service import MAX_NOTES_LENGTH


# --- Registration: password strength ---------------------------------

def test_register_rejects_short_password(client):
    r = client.post(
        "/api/auth/register",
        json={"name": "New Learner", "email": "short-pw@test.com", "password": "abc123", "role": "learner"},
    )
    assert r.status_code == 422
    assert len("abc123") < MIN_PASSWORD_LENGTH


def test_register_rejects_password_without_digit(client):
    r = client.post(
        "/api/auth/register",
        json={"name": "New Learner", "email": "letters-only@test.com", "password": "abcdefgh", "role": "learner"},
    )
    assert r.status_code == 422


def test_register_rejects_password_without_letter(client):
    r = client.post(
        "/api/auth/register",
        json={"name": "New Learner", "email": "digits-only@test.com", "password": "12345678", "role": "learner"},
    )
    assert r.status_code == 422


def test_register_accepts_reasonable_password(client):
    r = client.post(
        "/api/auth/register",
        json={"name": "New Learner", "email": "good-pw@test.com", "password": "correcthorse8", "role": "learner"},
    )
    assert r.status_code == 200
    assert r.json()["user"]["email"] == "good-pw@test.com"


def test_register_rejects_oversized_name(client):
    r = client.post(
        "/api/auth/register",
        json={
            "name": "x" * (MAX_NAME_LENGTH + 1),
            "email": "long-name@test.com",
            "password": "correcthorse8",
            "role": "learner",
        },
    )
    assert r.status_code == 422


# --- Existing users with old, weaker passwords must still be able to log in ---

def test_login_unaffected_by_new_password_rules(client, make_user, auth_headers):
    # make_user creates users through User(hashed_password=hash_password(...))
    # directly, bypassing UserCreate entirely — exactly like a real account
    # that predates this validation change. Login must still work for them.
    user = make_user("Legacy User", "legacy-pw-user@test.com", "learner")
    r = client.post("/api/auth/login", json={"email": user.email, "password": "test-password"})
    assert r.status_code == 200


# --- Instructor notes: length cap -------------------------------------

@pytest.fixture()
def note_roster(make_user, db_session):
    from app.models.instructor_learner import InstructorLearner
    from app.models.instructor_note import InstructorNote
    from app.services.instructor_service import add_learner_to_roster_by_id

    instructor = make_user("Note Instructor", "note-instructor@test.com", "instructor")
    learner = make_user("Note Learner", "note-learner@test.com", "learner")

    db_session.query(InstructorNote).filter(InstructorNote.learner_id == learner.id).delete()
    db_session.query(InstructorLearner).filter(InstructorLearner.instructor_id == instructor.id).delete()
    db_session.commit()
    add_learner_to_roster_by_id(db_session, instructor_id=instructor.id, learner_id=learner.id)

    return {"instructor": instructor, "learner": learner}


def test_note_rejects_oversized_text(client, note_roster, auth_headers):
    r = client.post(
        f"/api/instructor/learners/{note_roster['learner'].id}/notes",
        json={"note": "x" * (MAX_NOTE_LENGTH + 1)},
        headers=auth_headers(note_roster["instructor"]),
    )
    assert r.status_code == 422


def test_note_rejects_empty_text(client, note_roster, auth_headers):
    r = client.post(
        f"/api/instructor/learners/{note_roster['learner'].id}/notes",
        json={"note": ""},
        headers=auth_headers(note_roster["instructor"]),
    )
    assert r.status_code == 422


def test_note_accepts_text_at_the_limit(client, note_roster, auth_headers):
    r = client.post(
        f"/api/instructor/learners/{note_roster['learner'].id}/notes",
        json={"note": "x" * MAX_NOTE_LENGTH},
        headers=auth_headers(note_roster["instructor"]),
    )
    assert r.status_code == 200
    assert len(r.json()["note"]) == MAX_NOTE_LENGTH


# --- Assignment notes: length cap (multipart Form field) ---------------

@pytest.fixture()
def assignment_roster(make_user, db_session):
    from app.models.instructor_assignment import InstructorAssignment
    from app.models.instructor_learner import InstructorLearner
    from app.services.instructor_service import add_learner_to_roster_by_id

    instructor = make_user("Assignment Instructor", "assignment-instructor@test.com", "instructor")
    learner = make_user("Assignment Learner", "assignment-learner@test.com", "learner")

    db_session.query(InstructorAssignment).filter(InstructorAssignment.learner_id == learner.id).delete()
    db_session.query(InstructorLearner).filter(InstructorLearner.instructor_id == instructor.id).delete()
    db_session.commit()
    add_learner_to_roster_by_id(db_session, instructor_id=instructor.id, learner_id=learner.id)

    return {"instructor": instructor, "learner": learner}


def test_assignment_rejects_oversized_notes(client, assignment_roster, auth_headers):
    r = client.post(
        f"/api/instructor/learners/{assignment_roster['learner'].id}/assignments",
        data={"topic": "A", "topic_type": "letter", "notes": "x" * (MAX_NOTES_LENGTH + 1)},
        headers=auth_headers(assignment_roster["instructor"]),
    )
    assert r.status_code == 400


def test_assignment_accepts_reasonable_notes(client, assignment_roster, auth_headers):
    r = client.post(
        f"/api/instructor/learners/{assignment_roster['learner'].id}/assignments",
        data={"topic": "A", "topic_type": "letter", "notes": "Focus on hand shape."},
        headers=auth_headers(assignment_roster["instructor"]),
    )
    assert r.status_code == 200
    assert r.json()["notes"] == "Focus on hand shape."


# --- Certificate revoke reason: length cap ------------------------------

def test_revoke_rejects_oversized_reason(client, make_user, db_session, auth_headers):
    from app.models.certificate import Certificate
    from app.services.certificate_service import _create_certificate

    instructor = make_user("Revoke Instructor", "revoke-instructor@test.com", "instructor")
    learner = make_user("Revoke Learner", "revoke-learner@test.com", "learner")
    db_session.query(Certificate).filter(Certificate.learner_id == learner.id).delete()
    db_session.commit()

    from app.services.instructor_service import add_learner_to_roster_by_id
    add_learner_to_roster_by_id(db_session, instructor_id=instructor.id, learner_id=learner.id)

    cert = _create_certificate(db_session, learner.id, "alphabet-fundamentals", issued_by=instructor.id, issued_by_name=instructor.name)

    r = client.post(
        f"/api/instructor/certificates/{cert.id}/revoke",
        json={"reason": "x" * (MAX_REVOKE_REASON_LENGTH + 1)},
        headers=auth_headers(instructor),
    )
    assert r.status_code == 422
