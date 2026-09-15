"""
Milestone 4 test suite — Certification Workflows & Reporting Modules.
Run with:  pytest -v   (from backend/)
"""
from tests.conftest import register_and_login, seed_attempts

STRONG_LEARNER = {
    "OPEN_PALM": [88, 90, 92, 91, 93],
    "FIST": [88, 90, 92, 91, 93],
    "PEACE": [88, 90, 92, 91, 93],
    "THUMBS_UP": [88, 90, 92, 91, 93],
    "OK_SIGN": [88, 90, 92, 91, 93],
    "POINT": [88, 90, 92, 91, 93],
}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_certification_eligibility_starts_false(client):
    headers = register_and_login(client, "alice")
    r = client.get("/api/certification/eligibility", headers=headers)
    assert r.status_code == 200
    levels = r.json()["levels"]
    assert len(levels) == 4
    # Zero attempts logged -> nobody is eligible yet
    assert all(not lvl["eligible"] for lvl in levels)
    beginner = next(lvl for lvl in levels if lvl["level"] == "Beginner")
    assert "attempts" in beginner["reasons"][0]


def test_certification_eligibility_becomes_true_after_practice(client):
    headers = register_and_login(client, "bob")
    seed_attempts("bob", STRONG_LEARNER)
    r = client.get("/api/certification/eligibility", headers=headers)
    levels = {lvl["level"]: lvl for lvl in r.json()["levels"]}
    assert levels["Beginner"]["eligible"] is True
    assert levels["Intermediate"]["eligible"] is True
    # Only 6 distinct gestures practiced -> Advanced (needs 8) not yet eligible
    assert levels["Advanced"]["eligible"] is False


def test_issue_certificate_and_reject_duplicate(client):
    headers = register_and_login(client, "carol")
    seed_attempts("carol", STRONG_LEARNER)

    r = client.post("/api/certification/issue/Beginner", headers=headers)
    assert r.status_code == 200
    cert = r.json()
    assert cert["level"] == "Beginner"
    assert cert["certificate_code"].startswith("SLP-BEG-")

    # Issuing the same level again should be rejected
    r2 = client.post("/api/certification/issue/Beginner", headers=headers)
    assert r2.status_code == 409


def test_issue_certificate_rejects_when_not_eligible(client):
    headers = register_and_login(client, "dave")
    # No practice logged at all
    r = client.post("/api/certification/issue/Beginner", headers=headers)
    assert r.status_code == 400
    assert "reasons" in r.json()["detail"]


def test_certificate_verification_public(client):
    headers = register_and_login(client, "erin")
    seed_attempts("erin", STRONG_LEARNER)
    cert = client.post("/api/certification/issue/Beginner", headers=headers).json()

    # No auth header at all — verification must be public
    r = client.get(f"/api/certification/verify/{cert['certificate_code']}")
    assert r.status_code == 200
    body = r.json()
    assert body["valid"] is True
    assert body["username"] == "erin"

    r_bad = client.get("/api/certification/verify/NOT-A-REAL-CODE")
    assert r_bad.json()["valid"] is False


def test_certification_all_requires_staff_role(client):
    learner_headers = register_and_login(client, "frank", role="Learner")
    r = client.get("/api/certification/all", headers=learner_headers)
    assert r.status_code == 403

    instructor_headers = register_and_login(client, "grace", role="Instructor")
    r2 = client.get("/api/certification/all", headers=instructor_headers)
    assert r2.status_code == 200


def test_reports_learning_and_csv_exports(client):
    headers = register_and_login(client, "heidi")
    seed_attempts("heidi", STRONG_LEARNER)

    r = client.get("/api/reports/learning", headers=headers)
    assert r.status_code == 200
    assert r.json()["total_attempts"] == 30

    r = client.get("/api/reports/accuracy/csv", headers=headers)
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    assert "gesture,display_name" in r.text

    r = client.get("/api/reports/progress/csv", headers=headers)
    assert r.status_code == 200
    assert "attempt_no,gesture" in r.text

    r = client.get("/api/reports/certification/csv", headers=headers)
    assert r.status_code == 200
    assert "certificate_code" in r.text


def test_class_overview_requires_staff_role(client):
    learner_headers = register_and_login(client, "ivan")
    seed_attempts("ivan", STRONG_LEARNER)

    r = client.get("/api/reports/class-overview", headers=learner_headers)
    assert r.status_code == 403

    instructor_headers = register_and_login(client, "judy", role="Instructor")
    r2 = client.get("/api/reports/class-overview", headers=instructor_headers)
    assert r2.status_code == 200
    usernames = [row["username"] for row in r2.json()]
    assert "ivan" in usernames

    r3 = client.get("/api/reports/class-overview/csv", headers=instructor_headers)
    assert r3.status_code == 200
    assert "username,learning_level" in r3.text


def test_certificate_pdf_download(client):
    headers = register_and_login(client, "kate")
    seed_attempts("kate", STRONG_LEARNER)
    cert = client.post("/api/certification/issue/Beginner", headers=headers).json()

    r = client.get(f"/api/certification/{cert['id']}/download/pdf", headers=headers)
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
    assert r.content[:4] == b"%PDF"
    assert len(r.content) > 1000  # a real rendered PDF, not an empty stub


def test_report_pdf_downloads(client):
    headers = register_and_login(client, "liam")
    seed_attempts("liam", STRONG_LEARNER)

    for path in ["/api/reports/learning/pdf", "/api/reports/accuracy/pdf",
                 "/api/reports/progress/pdf", "/api/reports/certification/pdf"]:
        r = client.get(path, headers=headers)
        assert r.status_code == 200, path
        assert r.headers["content-type"] == "application/pdf", path
        assert r.content[:4] == b"%PDF", path


def test_class_overview_pdf_requires_staff_role(client):
    learner_headers = register_and_login(client, "mona")
    r = client.get("/api/reports/class-overview/pdf", headers=learner_headers)
    assert r.status_code == 403

    instructor_headers = register_and_login(client, "noah", role="Instructor")
    r2 = client.get("/api/reports/class-overview/pdf", headers=instructor_headers)
    assert r2.status_code == 200
    assert r2.content[:4] == b"%PDF"


def test_admin_can_set_learner_level(client):
    learner_headers = register_and_login(client, "olive")
    admin_headers = register_and_login(client, "pete", role="Administrator")

    from database import db
    olive = db.get_user_by_username("olive")

    r = client.put(f"/api/admin/users/{olive['id']}/level", json={"level": "Advanced"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["learning_level"] == "Advanced"

    # a non-admin can't do this
    r2 = client.put(f"/api/admin/users/{olive['id']}/level", json={"level": "Beginner"}, headers=learner_headers)
    assert r2.status_code == 403

    # invalid level rejected
    r3 = client.put(f"/api/admin/users/{olive['id']}/level", json={"level": "Not A Level"}, headers=admin_headers)
    assert r3.status_code == 400


def test_expanded_gesture_library_has_13_unique_signs(client):
    r = client.get("/api/gesture/library")
    assert r.status_code == 200
    library = r.json()
    assert len(library) == 13
    patterns = [tuple(g["pattern"]) for g in library]
    assert len(set(patterns)) == len(patterns)  # all unique, no ambiguous overlaps
