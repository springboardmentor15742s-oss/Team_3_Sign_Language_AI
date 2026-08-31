"""
End-to-end check of the "Assign a practice focus" feature (now including
optional reference photo/video attachments): an instructor creates an
assignment for a learner (a letter, a motion sign, a word sign — one with
a reference image, one with a reference video), lists it back, the
learner sees it via their own /assignments endpoint, the reference media
is actually servable at its /media/... URL, invalid topics/topic_types/
media are rejected, and deletion works (including cleaning up the
uploaded file from disk).

Run from backend/:
    python3 scripts/test_instructor_assignments.py
"""
import io
import sys

sys.path.insert(0, ".")

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import instructor_assignment, learning_activity, motion_sign_attempt, practice_attempt, word_sign_attempt  # noqa: F401
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password
from app.services.media_upload_service import UPLOAD_DIR

Base.metadata.create_all(bind=engine)
client = TestClient(app)

PASS = 0
FAIL = 0


def check(cond, label):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  OK   {label}")
    else:
        FAIL += 1
        print(f"  FAIL {label}")


def tiny_png_bytes():
    # A minimal valid 1x1 PNG, just enough to exercise the real upload/
    # storage path without needing a real asset on disk.
    return bytes.fromhex(
        "89504e470d0a1a0a0000000d4948445200000001000000010802000000907753"
        "de000000017352474200aece1ce90000000467414d410000b18f0bfc61050000"
        "00097048597300000ec300000ec301c76fa8640000000c4944415408d763f8ff"
        "ff3f0005fe02fea739666500000000496e444ae426082e"
    )


print("=== Create/reuse a test instructor + learner ===")
db = SessionLocal()

instructor_email = "assign-test-instructor@test.com"
instructor = db.query(User).filter(User.email == instructor_email).first()
if instructor is None:
    instructor = User(
        id="assign-test-instructor",
        name="Assign Test Instructor",
        email=instructor_email,
        hashed_password=hash_password("test-password"),
        role="instructor",
    )
    db.add(instructor)
    db.commit()

learner_email = "assign-test-learner@test.com"
learner = db.query(User).filter(User.email == learner_email).first()
if learner is None:
    learner = User(
        id="assign-test-learner",
        name="Assign Test Learner",
        email=learner_email,
        hashed_password=hash_password("test-password"),
        role="learner",
    )
    db.add(learner)
    db.commit()

# Clean up any leftover assignments from a prior run so counts are predictable.
db.query(instructor_assignment.InstructorAssignment).filter(
    instructor_assignment.InstructorAssignment.learner_id == learner.id
).delete()
db.commit()

instructor_id, instructor_name = instructor.id, instructor.name
learner_id = learner.id
db.close()

instructor_token = create_access_token({"sub": instructor_id})
learner_token = create_access_token({"sub": learner_id})
instructor_headers = {"Authorization": f"Bearer {instructor_token}"}
learner_headers = {"Authorization": f"Bearer {learner_token}"}

print("\n=== Instructor creates assignments (multipart form, some with reference media) ===")
resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "A", "topic_type": "letter"},
    files={"reference_media": ("handshape.png", tiny_png_bytes(), "image/png")},
    headers=instructor_headers,
)
check(resp.status_code == 200, f"create letter assignment with image -> 200 (got {resp.status_code}: {resp.text[:200]})")
letter_assignment_id = None
saved_media_path = None
if resp.status_code == 200:
    body = resp.json()
    check(body["topic"] == "A" and body["topic_type"] == "letter", "letter assignment fields correct")
    check(body["instructor_name"] == instructor_name, "instructor_name attached")
    check(body["reference_media_type"] == "image", f"reference_media_type == image (got {body['reference_media_type']})")
    check(
        bool(body["reference_media_url"]) and body["reference_media_url"].startswith("/media/assignments/"),
        f"reference_media_url looks right (got {body['reference_media_url']})",
    )
    letter_assignment_id = body["id"]
    saved_media_path = body["reference_media_url"]

    media_resp = client.get(saved_media_path)
    check(media_resp.status_code == 200, f"uploaded image is servable at {saved_media_path} -> 200 (got {media_resp.status_code})")
    check(media_resp.content == tiny_png_bytes(), "served image bytes match what was uploaded")

resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "Wave", "topic_type": "motion_sign"},
    files={"reference_media": ("wave.mp4", b"not-a-real-mp4-but-fine-for-this-check", "video/mp4")},
    headers=instructor_headers,
)
check(resp.status_code == 200, f"create motion_sign assignment with video -> 200 (got {resp.status_code}: {resp.text[:200]})")
if resp.status_code == 200:
    check(resp.json()["reference_media_type"] == "video", "reference_media_type == video")

resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "practice", "topic_type": "word_sign"},
    headers=instructor_headers,
)
check(resp.status_code == 200, f"create word_sign assignment with no media -> 200 (got {resp.status_code}: {resp.text[:200]})")
if resp.status_code == 200:
    body = resp.json()
    check(body["reference_media_url"] is None, "no media -> reference_media_url is null")
    check(body["reference_media_type"] is None, "no media -> reference_media_type is null")

print("\n=== Invalid assignments / media are rejected ===")
resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "ZZZ", "topic_type": "letter"},
    headers=instructor_headers,
)
check(resp.status_code == 400, f"unsupported letter -> 400 (got {resp.status_code})")

resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "A", "topic_type": "nonsense"},
    headers=instructor_headers,
)
check(resp.status_code == 400, f"unknown topic_type -> 400 (got {resp.status_code})")

resp = client.post(
    "/api/instructor/learners/does-not-exist/assignments",
    data={"topic": "A", "topic_type": "letter"},
    headers=instructor_headers,
)
check(resp.status_code == 400, f"unknown learner -> 400 (got {resp.status_code})")

resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "B", "topic_type": "letter"},
    files={"reference_media": ("notes.txt", b"plain text is not an allowed media type", "text/plain")},
    headers=instructor_headers,
)
check(resp.status_code == 400, f"unsupported media content-type -> 400 (got {resp.status_code})")

resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "C", "topic_type": "letter"},
    files={"reference_media": ("huge.png", b"0" * (21 * 1024 * 1024), "image/png")},
    headers=instructor_headers,
)
check(resp.status_code == 400, f"oversized media (21MB) -> 400 (got {resp.status_code})")

print("\n=== Learner cannot create assignments (instructor-only) ===")
resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "A", "topic_type": "letter"},
    headers=learner_headers,
)
check(resp.status_code == 403, f"learner blocked from creating -> 403 (got {resp.status_code})")

print("\n=== Instructor lists assignments ===")
resp = client.get(f"/api/instructor/learners/{learner_id}/assignments", headers=instructor_headers)
check(resp.status_code == 200, f"instructor list -> 200 (got {resp.status_code})")
if resp.status_code == 200:
    assignments = resp.json()["assignments"]
    check(len(assignments) == 3, f"3 assignments present (got {len(assignments)})")
    check(assignments[0]["created_at"] >= assignments[-1]["created_at"], "newest first")

print("\n=== Learner sees their own assignments (including media fields) ===")
resp = client.get(f"/api/learner/{learner_id}/assignments", headers=learner_headers)
check(resp.status_code == 200, f"learner self-view -> 200 (got {resp.status_code})")
if resp.status_code == 200:
    learner_assignments = resp.json()["assignments"]
    check(len(learner_assignments) == 3, "learner sees all 3 assignments")
    by_topic = {a["topic"]: a for a in learner_assignments}
    check(by_topic["A"]["reference_media_type"] == "image", "learner view: A has image media")
    check(by_topic["Wave"]["reference_media_type"] == "video", "learner view: Wave has video media")
    check(by_topic["practice"]["reference_media_url"] is None, "learner view: practice has no media")

print("\n=== Instructor can view any learner's assignments too (require_self_or_staff) ===")
resp = client.get(f"/api/learner/{learner_id}/assignments", headers=instructor_headers)
check(resp.status_code == 200, f"instructor via learner route -> 200 (got {resp.status_code})")

print("\n=== Delete an assignment cleans up its media file from disk ===")
if letter_assignment_id and saved_media_path:
    disk_path = UPLOAD_DIR / saved_media_path.rsplit("/", 1)[-1]
    check(disk_path.exists(), f"uploaded file exists on disk before delete ({disk_path})")

    resp = client.delete(f"/api/instructor/assignments/{letter_assignment_id}", headers=instructor_headers)
    check(resp.status_code == 200, f"delete -> 200 (got {resp.status_code})")

    check(not disk_path.exists(), "uploaded file removed from disk after delete")

    resp = client.get(f"/api/learner/{learner_id}/assignments", headers=learner_headers)
    check(len(resp.json()["assignments"]) == 2, "2 assignments remain after delete")

    resp = client.delete(f"/api/instructor/assignments/{letter_assignment_id}", headers=instructor_headers)
    check(resp.status_code == 404, f"deleting again -> 404 (got {resp.status_code})")

print(f"\n=== {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
