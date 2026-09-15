"""
Tests for this session's additions:
  - Weighted Learning Performance Score  (/api/intelligence/performance-score)
  - Quiz / Knowledge-Check module        (/api/quiz/*)
  - Certificate revocation                (/api/certification/{id}/status)
  - Admin announcement posting is already covered in test_notifications.py

Run with: pytest tests/test_score_quiz_admin.py -v   (from backend/)
"""
from tests.conftest import register_and_login, seed_attempts

STRONG_LEARNER = {
    "OPEN_PALM": [88, 90, 92, 91, 93],
    "FIST": [88, 90, 92, 91, 93],
    "PEACE": [88, 90, 92, 91, 93],
    "THUMBS_UP": [88, 90, 92, 91, 93],
    "POINTING": [88, 90, 92, 91, 93],
    "LETTER_L": [88, 90, 92, 91, 93],
}


# ---------------------------------------------------------------------
# Weighted Learning Performance Score
# ---------------------------------------------------------------------
def test_performance_score_zero_state_for_new_user(client):
    headers = register_and_login(client, "score_newbie")
    r = client.get("/api/intelligence/performance-score", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["has_data"] is False
    # No gesture data yet -> gesture/assessment/lesson/consistency components are 0,
    # but skill_improvement_rate defaults to a neutral 50 (not enough data to judge).
    by_key = {c["key"]: c["value"] for c in body["components"]}
    assert by_key["gesture_accuracy"] == 0.0
    assert by_key["skill_improvement_rate"] == 50.0
    assert body["learning_performance_score"] == 5.0  # 50 * 10% weight, everything else 0


def test_performance_score_reflects_practice(client):
    headers = register_and_login(client, "score_practicer")
    seed_attempts("score_practicer", STRONG_LEARNER)

    r = client.get("/api/intelligence/performance-score", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["has_data"] is True
    by_key = {c["key"]: c["value"] for c in body["components"]}
    assert by_key["gesture_accuracy"] > 80
    # Weights sum to 100%, so the composite score is bounded 0-100.
    assert 0 <= body["learning_performance_score"] <= 100


def test_performance_score_weights_sum_to_100_percent(client):
    headers = register_and_login(client, "score_weights")
    r = client.get("/api/intelligence/performance-score", headers=headers)
    total_weight = sum(c["weight_percent"] for c in r.json()["components"])
    assert total_weight == 100


def test_performance_score_included_in_summary(client):
    headers = register_and_login(client, "score_summary")
    r = client.get("/api/intelligence/summary", headers=headers)
    assert r.status_code == 200
    assert "performance_score" in r.json()


# ---------------------------------------------------------------------
# Quiz / Knowledge-Check module
# ---------------------------------------------------------------------
def test_get_quiz_questions_excludes_answer_key(client):
    headers = register_and_login(client, "quiz_taker1")
    r = client.get("/api/quiz/questions", params={"level": "Beginner", "count": 3}, headers=headers)
    assert r.status_code == 200
    questions = r.json()
    assert len(questions) == 3
    for q in questions:
        assert "correct_option" not in q
        assert "explanation" not in q
        assert set(["option_a", "option_b", "option_c", "option_d"]).issubset(q.keys())


def test_quiz_invalid_level_rejected(client):
    headers = register_and_login(client, "quiz_taker2")
    r = client.get("/api/quiz/questions", params={"level": "Expert"}, headers=headers)
    assert r.status_code == 400


def test_quiz_submit_grades_correctly_and_logs_attempt(client):
    headers = register_and_login(client, "quiz_taker3")
    questions = client.get(
        "/api/quiz/questions", params={"level": "Beginner", "count": 5}, headers=headers
    ).json()

    # Deliberately answer everything with option 'a' — score depends on how many
    # actually have correct_option == 'a', but the point is grading is server-side
    # and the attempt gets persisted regardless of the score.
    answers = [{"question_id": q["id"], "selected_option": "a"} for q in questions]
    r = client.post(
        "/api/quiz/submit", json={"level": "Beginner", "answers": answers}, headers=headers
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 5
    assert 0 <= body["score"] <= 5
    assert len(body["results"]) == 5
    for result in body["results"]:
        assert "correct_option" in result
        assert "explanation" in result

    history = client.get("/api/quiz/my-attempts", headers=headers).json()
    assert len(history) == 1
    assert history[0]["total_questions"] == 5


def test_quiz_requires_auth(client):
    r = client.get("/api/quiz/questions", params={"level": "Beginner"})
    assert r.status_code == 401


# ---------------------------------------------------------------------
# Certificate revocation
# ---------------------------------------------------------------------
def test_revoke_certificate_requires_admin(client):
    learner_headers = register_and_login(client, "cert_learner")
    seed_attempts("cert_learner", STRONG_LEARNER)
    cert = client.post("/api/certification/issue/Beginner", headers=learner_headers).json()

    # A learner (non-admin) cannot revoke
    r = client.put(
        f"/api/certification/{cert['id']}/status", json={"status": "Revoked"}, headers=learner_headers
    )
    assert r.status_code == 403


def test_admin_can_revoke_and_reactivate_certificate(client):
    learner_headers = register_and_login(client, "cert_learner2")
    admin_headers = register_and_login(client, "cert_admin", role="Administrator")
    seed_attempts("cert_learner2", STRONG_LEARNER)
    cert = client.post("/api/certification/issue/Beginner", headers=learner_headers).json()

    r = client.put(
        f"/api/certification/{cert['id']}/status", json={"status": "Revoked"}, headers=admin_headers
    )
    assert r.status_code == 200
    assert r.json()["status"] == "Revoked"

    # Verify endpoint (public) reflects the revocation
    v = client.get(f"/api/certification/verify/{cert['certificate_code']}")
    assert v.json()["valid"] is False
    assert v.json()["status"] == "Revoked"

    # Reactivate
    r2 = client.put(
        f"/api/certification/{cert['id']}/status", json={"status": "Active"}, headers=admin_headers
    )
    assert r2.status_code == 200
    assert r2.json()["status"] == "Active"


def test_revoke_rejects_invalid_status(client):
    learner_headers = register_and_login(client, "cert_learner3")
    admin_headers = register_and_login(client, "cert_admin2", role="Administrator")
    seed_attempts("cert_learner3", STRONG_LEARNER)
    cert = client.post("/api/certification/issue/Beginner", headers=learner_headers).json()

    r = client.put(
        f"/api/certification/{cert['id']}/status", json={"status": "Deleted"}, headers=admin_headers
    )
    assert r.status_code == 400
