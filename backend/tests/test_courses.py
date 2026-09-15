"""
Course & Content Service test suite — catalog, watch/progress, and
instructor-only course/lesson creation (RBAC).

Run with:  pytest tests/test_courses.py -v   (from backend/)

Note: main.py seeds 6 starter courses / 17 lessons on the FastAPI app's
startup event, which TestClient triggers as a context manager (see
tests/conftest.py's `client` fixture) — so every test here starts from that
seeded catalog, exactly like a real first run.
"""
from tests.conftest import register_and_login


def test_seeded_catalog_is_present(client):
    headers = register_and_login(client, "cat_learner")
    r = client.get("/api/courses", headers=headers)
    assert r.status_code == 200
    courses = r.json()
    assert len(courses) == 10
    categories = {c["category"] for c in courses}
    assert categories == {
        "Beginner Sign Language",
        "Intermediate Sign Language",
        "Advanced Sign Language",
        "Everyday Communication",
        "Educational Vocabulary",
        "Professional Communication",
    }


def test_filter_by_category_and_level(client):
    headers = register_and_login(client, "filter_learner")
    r = client.get("/api/courses", params={"category": "Professional Communication"}, headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 2

    r = client.get("/api/courses", params={"level": "Beginner"}, headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 3


def test_search_filter(client):
    headers = register_and_login(client, "search_learner")
    r = client.get("/api/courses", params={"search": "Colors"}, headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert "Colors" in r.json()[0]["title"]


def test_course_detail_has_lessons_and_progress_fields(client):
    headers = register_and_login(client, "detail_learner")
    course_id = client.get("/api/courses", headers=headers).json()[0]["id"]
    r = client.get(f"/api/courses/{course_id}", headers=headers)
    assert r.status_code == 200
    detail = r.json()
    assert detail["lessons"], "expected seeded lessons on the first course"
    assert detail["is_enrolled"] is False
    assert detail["progress_percent"] == 0.0
    assert all("watched" in lesson for lesson in detail["lessons"])


def test_unknown_course_404s(client):
    headers = register_and_login(client, "notfound_learner")
    r = client.get("/api/courses/999999", headers=headers)
    assert r.status_code == 404


def test_enroll_then_mark_lesson_watched_updates_progress(client):
    headers = register_and_login(client, "watch_learner")
    course = client.get("/api/courses", headers=headers).json()[0]
    course_id = course["id"]

    r = client.post(f"/api/courses/{course_id}/enroll", headers=headers)
    assert r.status_code == 200
    assert r.json()["enrolled"] is True

    lesson_id = client.get(f"/api/courses/{course_id}", headers=headers).json()["lessons"][0]["id"]
    r = client.post(f"/api/courses/lessons/{lesson_id}/watched", headers=headers)
    assert r.status_code == 200
    progress = r.json()
    assert progress["watched_lessons"] == 1
    assert progress["percent"] > 0

    detail = client.get(f"/api/courses/{course_id}", headers=headers).json()
    assert detail["watched_lessons"] == 1
    assert detail["lessons"][0]["watched"] is True


def test_marking_lesson_watched_auto_enrolls_without_prior_enroll_call(client):
    headers = register_and_login(client, "autoenroll_learner")
    course = client.get("/api/courses", headers=headers).json()[1]
    course_id = course["id"]
    lesson_id = client.get(f"/api/courses/{course_id}", headers=headers).json()["lessons"][0]["id"]

    # No explicit /enroll call first.
    r = client.post(f"/api/courses/lessons/{lesson_id}/watched", headers=headers)
    assert r.status_code == 200

    detail = client.get(f"/api/courses/{course_id}", headers=headers).json()
    assert detail["is_enrolled"] is True


def test_my_enrollments_lists_enrolled_courses(client):
    headers = register_and_login(client, "myenroll_learner")
    course_id = client.get("/api/courses", headers=headers).json()[0]["id"]
    client.post(f"/api/courses/{course_id}/enroll", headers=headers)

    r = client.get("/api/courses/my-enrollments", headers=headers)
    assert r.status_code == 200
    enrollments = r.json()
    assert len(enrollments) == 1
    assert enrollments[0]["lesson_count"] >= 1
    assert enrollments[0]["watched_count"] == 0


def test_learner_cannot_create_course(client):
    headers = register_and_login(client, "learner_no_perms", role="Learner")
    r = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Should Fail",
            "description": "x",
            "category": "Beginner Sign Language",
            "level": "Beginner",
        },
    )
    assert r.status_code == 403


def test_instructor_can_create_course_and_add_lesson(client):
    headers = register_and_login(client, "instructor_1", role="Instructor")
    r = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Restaurant & Food Vocabulary",
            "description": "Ordering food, menus, and dining-related signs.",
            "category": "Everyday Communication",
            "level": "Beginner",
            "thumbnail_emoji": "🍽️",
        },
    )
    assert r.status_code == 201
    course_id = r.json()["id"]

    r = client.post(
        f"/api/courses/{course_id}/lessons",
        headers=headers,
        json={
            "title": "Ordering at a Restaurant",
            "description": "Core restaurant vocabulary.",
            "video_id": "dQw4w9WgXcQ",
            "duration_seconds": 240,
        },
    )
    assert r.status_code == 201
    assert r.json()["video_id"] == "dQw4w9WgXcQ"

    r = client.get("/api/courses", headers=headers)
    assert len(r.json()) == 11  # 10 seeded + this new one


def test_accessibility_trainer_and_admin_can_also_manage_courses(client):
    for role in ["Accessibility Trainer", "Administrator"]:
        headers = register_and_login(client, f"manager_{role.replace(' ', '_')}", role=role)
        r = client.post(
            "/api/courses",
            headers=headers,
            json={
                "title": f"Course by {role}",
                "description": "x",
                "category": "Beginner Sign Language",
                "level": "Beginner",
            },
        )
        assert r.status_code == 201, f"{role} should be allowed to create courses"


def test_invalid_category_or_level_rejected(client):
    headers = register_and_login(client, "bad_input_instructor", role="Instructor")
    r = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Bad Category Course",
            "description": "x",
            "category": "Not A Real Category",
            "level": "Beginner",
        },
    )
    assert r.status_code == 400

    r = client.post(
        "/api/courses",
        headers=headers,
        json={
            "title": "Bad Level Course",
            "description": "x",
            "category": "Beginner Sign Language",
            "level": "Not A Real Level",
        },
    )
    assert r.status_code == 400


def test_course_meta_returns_category_and_level_options(client):
    headers = register_and_login(client, "meta_learner")
    r = client.get("/api/courses/meta", headers=headers)
    assert r.status_code == 200
    body = r.json()
    assert len(body["categories"]) == 6
    assert len(body["levels"]) == 4
