"""
Notification & Reminder System tests — roadmap section 12.
Run with: pytest -v  (from backend/)
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


def test_notifications_start_empty(client):
    headers = register_and_login(client, "quinn")
    r = client.get("/api/notifications", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert body["notifications"] == []
    assert body["unread_count"] == 0


def test_achievement_notification_on_certificate_issue(client):
    headers = register_and_login(client, "riley")
    seed_attempts("riley", STRONG_LEARNER)
    client.post("/api/certification/issue/Beginner", headers=headers)

    r = client.get("/api/notifications", headers=headers)
    body = r.json()
    assert body["unread_count"] >= 1
    types = [n["type"] for n in body["notifications"]]
    assert "achievement" in types
    achievement = next(n for n in body["notifications"] if n["type"] == "achievement")
    assert "Beginner" in achievement["title"]


def test_course_completion_notification(client):
    headers = register_and_login(client, "sam")

    courses = client.get("/api/courses", headers=headers).json()
    assert len(courses) > 0, "expected seeded course catalog"
    course_id = courses[0]["id"]

    detail = client.get(f"/api/courses/{course_id}", headers=headers).json()
    client.post(f"/api/courses/{course_id}/enroll", headers=headers)

    lessons = detail["lessons"]
    assert len(lessons) > 0

    # Watch every lesson except the last — no completion notification yet
    for lesson in lessons[:-1]:
        client.post(f"/api/courses/lessons/{lesson['id']}/watched", headers=headers)

    r = client.get("/api/notifications", headers=headers)
    types_before = [n["type"] for n in r.json()["notifications"]]
    assert "course_completion" not in types_before

    # Watch the final lesson -> should cross 100% and fire the notification
    client.post(f"/api/courses/lessons/{lessons[-1]['id']}/watched", headers=headers)

    r2 = client.get("/api/notifications", headers=headers)
    types_after = [n["type"] for n in r2.json()["notifications"]]
    assert "course_completion" in types_after


def test_mark_read_and_mark_all_read(client):
    headers = register_and_login(client, "tara")
    seed_attempts("tara", STRONG_LEARNER)
    client.post("/api/certification/issue/Beginner", headers=headers)

    body = client.get("/api/notifications", headers=headers).json()
    assert body["unread_count"] >= 1
    notif_id = body["notifications"][0]["id"]

    r = client.post(f"/api/notifications/{notif_id}/read", headers=headers)
    assert r.status_code == 200

    r2 = client.post("/api/notifications/read-all", headers=headers)
    assert r2.status_code == 200

    body2 = client.get("/api/notifications", headers=headers).json()
    assert body2["unread_count"] == 0


def test_announcement_requires_admin_and_broadcasts_to_everyone(client):
    learner_headers = register_and_login(client, "uma")
    admin_headers = register_and_login(client, "victor", role="Administrator")

    # Non-admin can't post an announcement
    r = client.post(
        "/api/notifications/announcement",
        json={"title": "Maintenance", "message": "Downtime tonight."},
        headers=learner_headers,
    )
    assert r.status_code == 403

    # Admin can
    r2 = client.post(
        "/api/notifications/announcement",
        json={"title": "New Course Live!", "message": "Check out Advanced ASL."},
        headers=admin_headers,
    )
    assert r2.status_code == 200

    # A totally different learner should see the broadcast too
    other_headers = register_and_login(client, "wendy")
    r3 = client.get("/api/notifications", headers=other_headers)
    titles = [n["title"] for n in r3.json()["notifications"]]
    assert "New Course Live!" in titles


def test_unread_count_endpoint(client):
    headers = register_and_login(client, "xena")
    seed_attempts("xena", STRONG_LEARNER)
    client.post("/api/certification/issue/Beginner", headers=headers)

    r = client.get("/api/notifications/unread-count", headers=headers)
    assert r.status_code == 200
    assert r.json()["unread_count"] >= 1
