"""
Covers the certification workflow: auto-issuance the moment a learner
passes every item in a course (app/services/certificate_service.py),
manual staff issuance and roster-scoped revoke (app/routers/instructor.py),
and the public no-auth verification endpoint.
"""

import uuid

import pytest


@pytest.fixture()
def roster(make_user, db_session):
    from app.models.certificate import Certificate
    from app.models.instructor_learner import InstructorLearner
    from app.models.motion_sign_attempt import MotionSignAttempt
    from app.services.instructor_service import add_learner_to_roster_by_id

    instructor = make_user("Cert Instructor", "cert-instructor@test.com", "instructor")
    instructor2 = make_user("Cert Instructor Two", "cert-instructor-2@test.com", "instructor")
    admin = make_user("Cert Admin", "cert-admin@test.com", "admin")
    learner = make_user("Cert Learner", "cert-learner@test.com", "learner")
    learner2 = make_user("Second Cert Learner", "cert-learner-2@test.com", "learner")

    db_session.query(Certificate).filter(Certificate.learner_id.in_([learner.id, learner2.id])).delete(synchronize_session=False)
    db_session.query(MotionSignAttempt).filter(MotionSignAttempt.learner_id == learner.id).delete()
    db_session.query(InstructorLearner).filter(
        InstructorLearner.instructor_id.in_([instructor.id, instructor2.id])
    ).delete(synchronize_session=False)
    db_session.commit()
    add_learner_to_roster_by_id(db_session, instructor_id=instructor.id, learner_id=learner.id)

    # Directly seed both everyday-gestures signs as PASS — bypasses the
    # real video recognition pipeline, since this is testing certificate
    # eligibility logic, not the recognizer itself.
    for sign in ("Wave", "Clap"):
        db_session.add(MotionSignAttempt(
            id=str(uuid.uuid4()), learner_id=learner.id, target_sign=sign,
            predicted_sign=sign, status="pass", correct=True, confidence=None,
        ))
    db_session.commit()

    return {"instructor": instructor, "instructor2": instructor2, "admin": admin, "learner": learner, "learner2": learner2}


def test_completion_status_reflects_real_progress(client, roster, auth_headers):
    r = client.get(f"/api/certificates/learner/{roster['learner'].id}/status", headers=auth_headers(roster["learner"]))
    assert r.status_code == 200
    statuses = {c["course_id"]: c for c in r.json()["courses"]}
    assert len(statuses) == 3
    assert statuses["everyday-gestures"]["eligible"] is True
    assert statuses["everyday-gestures"]["already_issued"] is False
    assert statuses["alphabet-fundamentals"]["eligible"] is False


def test_auto_issuance_on_list_and_no_duplicates(client, roster, auth_headers):
    learner_headers = auth_headers(roster["learner"])
    learner_id = roster["learner"].id

    r = client.get(f"/api/certificates/learner/{learner_id}", headers=learner_headers)
    assert r.status_code == 200
    certs = r.json()["certificates"]
    assert len(certs) == 1
    assert certs[0]["course_id"] == "everyday-gestures"
    assert certs[0]["issued_by"] == "system"
    assert len(certs[0]["verification_code"]) == 10
    assert certs[0]["revoked"] is False

    # Re-listing must not create a duplicate.
    r = client.get(f"/api/certificates/learner/{learner_id}", headers=learner_headers)
    assert len(r.json()["certificates"]) == 1


def test_learner_cannot_see_another_learners_certificates(client, roster, auth_headers):
    r = client.get(f"/api/certificates/learner/{roster['learner'].id}", headers=auth_headers(roster["learner2"]))
    assert r.status_code == 403


def test_certificate_pdf_download(client, roster, auth_headers):
    learner_id = roster["learner"].id
    learner_headers = auth_headers(roster["learner"])
    cert = client.get(f"/api/certificates/learner/{learner_id}", headers=learner_headers).json()["certificates"][0]

    r = client.get(f"/api/certificates/learner/{learner_id}/{cert['id']}/pdf", headers=learner_headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert len(r.content) > 500

    # Staff on the learner's roster can also pull it.
    r = client.get(f"/api/certificates/learner/{learner_id}/{cert['id']}/pdf", headers=auth_headers(roster["instructor"]))
    assert r.status_code == 200


def test_public_verification(client, roster, auth_headers):
    learner_id = roster["learner"].id
    cert = client.get(f"/api/certificates/learner/{learner_id}", headers=auth_headers(roster["learner"])).json()["certificates"][0]

    r = client.get(f"/api/certificates/verify/{cert['verification_code']}")
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["learner_name"] == "Cert Learner"
    assert body["course_title"] == "Everyday Gestures"

    # Case-insensitive.
    r = client.get(f"/api/certificates/verify/{cert['verification_code'].lower()}")
    assert r.json()["valid"] is True

    r = client.get("/api/certificates/verify/NOTAREALCODE")
    assert r.status_code == 200
    assert r.json()["valid"] is False


def test_manual_issuance_and_roster_scoping(client, roster, auth_headers):
    learner_id = roster["learner"].id
    instructor_headers = auth_headers(roster["instructor"])
    instructor2_headers = auth_headers(roster["instructor2"])
    admin_headers = auth_headers(roster["admin"])

    r = client.post(
        f"/api/instructor/learners/{learner_id}/certificates",
        json={"course_id": "alphabet-fundamentals"},
        headers=instructor_headers,
    )
    assert r.status_code == 200
    cert = r.json()
    assert cert["issued_by"] == roster["instructor"].id
    assert cert["issued_by_name"] == "Cert Instructor"

    # Duplicate for the same (learner, course).
    r = client.post(
        f"/api/instructor/learners/{learner_id}/certificates",
        json={"course_id": "alphabet-fundamentals"},
        headers=instructor_headers,
    )
    assert r.status_code == 400

    # Non-certifiable course.
    r = client.post(
        f"/api/instructor/learners/{learner_id}/certificates",
        json={"course_id": "common-signs"},
        headers=instructor_headers,
    )
    assert r.status_code == 400

    # An instructor not on the learner's roster is blocked.
    r = client.post(
        f"/api/instructor/learners/{learner_id}/certificates",
        json={"course_id": "conversational-fluency"},
        headers=instructor2_headers,
    )
    assert r.status_code == 400

    # An admin is exempt from roster scoping.
    r = client.post(
        f"/api/instructor/learners/{learner_id}/certificates",
        json={"course_id": "conversational-fluency"},
        headers=admin_headers,
    )
    assert r.status_code == 200


def test_revoke_is_roster_scoped_and_reflected_in_verification(client, roster, auth_headers):
    learner_id = roster["learner"].id
    instructor_headers = auth_headers(roster["instructor"])
    instructor2_headers = auth_headers(roster["instructor2"])

    cert = client.post(
        f"/api/instructor/learners/{learner_id}/certificates",
        json={"course_id": "alphabet-fundamentals"},
        headers=instructor_headers,
    ).json()

    r = client.post(
        f"/api/instructor/certificates/{cert['id']}/revoke",
        json={"reason": "Issued by mistake during testing"},
        headers=instructor2_headers,
    )
    assert r.status_code == 400

    r = client.post(
        f"/api/instructor/certificates/{cert['id']}/revoke",
        json={"reason": "Issued by mistake during testing"},
        headers=instructor_headers,
    )
    assert r.status_code == 200
    assert r.json()["revoked"] is True

    r = client.get(f"/api/certificates/verify/{cert['verification_code']}")
    body = r.json()
    assert body["valid"] is False
    assert body["revoked"] is True
    assert body["course_title"] is not None  # revoked, not "unknown"
