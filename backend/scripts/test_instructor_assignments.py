"""
End-to-end check of the instructor-side feature set built around
InstructorAssignment: roster ownership (instructors only manage learners
they've added), assignments (topic + optional notes/due date/reference
media, bulk-assign to several learners, learner-driven completion),
instructor-only notes on a learner's profile, and class-wide analytics
aggregated across an instructor's roster.

Run from backend/:
    python3 scripts/test_instructor_assignments.py
"""
import io
import sys

sys.path.insert(0, ".")

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import (  # noqa: F401
    instructor_assignment,
    instructor_learner,
    instructor_note,
    learning_activity,
    motion_sign_attempt,
    practice_attempt,
    word_sign_attempt,
)
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


def get_or_create_user(db, id_, name, email, role):
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        user = User(id=id_, name=name, email=email, hashed_password=hash_password("test-password"), role=role)
        db.add(user)
        db.commit()
    return user


print("=== Create/reuse test users ===")
db = SessionLocal()

instructor = get_or_create_user(db, "assign-test-instructor", "Assign Test Instructor", "assign-test-instructor@test.com", "instructor")
instructor2 = get_or_create_user(db, "assign-test-instructor-2", "Second Instructor", "assign-test-instructor-2@test.com", "instructor")
admin = get_or_create_user(db, "assign-test-admin", "Assign Test Admin", "assign-test-admin@test.com", "admin")
learner = get_or_create_user(db, "assign-test-learner", "Assign Test Learner", "assign-test-learner@test.com", "learner")
learner2 = get_or_create_user(db, "assign-test-learner-2", "Second Learner", "assign-test-learner-2@test.com", "learner")

# Clean up leftover state from a prior run so counts are predictable.
from app.models.instructor_assignment import InstructorAssignment
from app.models.instructor_learner import InstructorLearner
from app.models.instructor_note import InstructorNote

for learner_row in (learner, learner2):
    db.query(InstructorAssignment).filter(InstructorAssignment.learner_id == learner_row.id).delete()
    db.query(InstructorNote).filter(InstructorNote.learner_id == learner_row.id).delete()
db.query(InstructorLearner).filter(
    InstructorLearner.instructor_id.in_([instructor.id, instructor2.id])
).delete(synchronize_session=False)
db.commit()

instructor_id, instructor_name = instructor.id, instructor.name
instructor2_id = instructor2.id
admin_id = admin.id
learner_id, learner2_id = learner.id, learner2.id
db.close()

instructor_headers = {"Authorization": f"Bearer {create_access_token({'sub': instructor_id})}"}
instructor2_headers = {"Authorization": f"Bearer {create_access_token({'sub': instructor2_id})}"}
admin_headers = {"Authorization": f"Bearer {create_access_token({'sub': admin_id})}"}
learner_headers = {"Authorization": f"Bearer {create_access_token({'sub': learner_id})}"}
learner2_headers = {"Authorization": f"Bearer {create_access_token({'sub': learner2_id})}"}

print("\n=== Roster ownership: starts empty, add-by-email, unknown email rejected ===")
resp = client.get("/api/instructor/learners", headers=instructor_headers)
check(resp.status_code == 200 and resp.json()["learners"] == [], "instructor roster starts empty")

resp = client.post("/api/instructor/learners", json={"learner_email": "nobody@nowhere.test"}, headers=instructor_headers)
check(resp.status_code == 400, f"adding unknown email -> 400 (got {resp.status_code})")

resp = client.post("/api/instructor/learners", json={"learner_email": learner.email}, headers=instructor_headers)
check(resp.status_code == 200, f"add learner to roster -> 200 (got {resp.status_code})")
if resp.status_code == 200:
    emails = [l["email"] for l in resp.json()["learners"]]
    check(learner.email in emails, "roster now includes the added learner")

resp = client.post("/api/instructor/learners", json={"learner_email": learner.email}, headers=instructor_headers)
check(resp.status_code == 200 and len(resp.json()["learners"]) == 1, "re-adding the same learner is a safe no-op")

print("\n=== Assignments blocked for a learner not yet on the roster ===")
resp = client.post(
    f"/api/instructor/learners/{learner2_id}/assignments",
    data={"topic": "A", "topic_type": "letter"},
    headers=instructor_headers,
)
check(resp.status_code == 400, f"assign to non-roster learner -> 400 (got {resp.status_code})")

resp = client.post("/api/instructor/learners", json={"learner_email": learner2.email}, headers=instructor_headers)
check(resp.status_code == 200, "add second learner to roster")

print("\n=== Cross-instructor isolation ===")
resp = client.get("/api/instructor/learners", headers=instructor2_headers)
check(resp.status_code == 200 and resp.json()["learners"] == [], "a different instructor's roster is empty (not shared)")

resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "A", "topic_type": "letter"},
    headers=instructor2_headers,
)
check(resp.status_code == 400, f"instructor2 cannot assign to instructor1's learner -> 400 (got {resp.status_code})")

print("\n=== Admin bypasses roster ownership entirely ===")
resp = client.get("/api/instructor/learners", headers=admin_headers)
check(resp.status_code == 200, f"admin roster -> 200 (got {resp.status_code})")
if resp.status_code == 200:
    admin_emails = {l["email"] for l in resp.json()["learners"]}
    check({learner.email, learner2.email} <= admin_emails, "admin sees every learner regardless of roster")

print("\n=== Instructor creates assignments (notes, due date, reference media) ===")
resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "A", "topic_type": "letter", "notes": "Focus on hand orientation, not speed.", "due_date": "2026-09-01"},
    files={"reference_media": ("handshape.png", tiny_png_bytes(), "image/png")},
    headers=instructor_headers,
)
check(resp.status_code == 200, f"create letter assignment -> 200 (got {resp.status_code}: {resp.text[:200]})")
letter_assignment_id = None
saved_media_path = None
if resp.status_code == 200:
    body = resp.json()
    check(body["notes"] == "Focus on hand orientation, not speed.", "notes saved")
    check(body["due_date"] == "2026-09-01", "due_date saved")
    check(body["completed"] is False and body["completed_at"] is None, "new assignment starts not completed")
    check(body["reference_media_type"] == "image", "reference_media_type == image")
    letter_assignment_id = body["id"]
    saved_media_path = body["reference_media_url"]

    media_resp = client.get(saved_media_path)
    check(media_resp.status_code == 200 and media_resp.content == tiny_png_bytes(), "uploaded image servable and byte-identical")

resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "A", "topic_type": "letter", "due_date": "not-a-date"},
    headers=instructor_headers,
)
check(resp.status_code == 400, f"malformed due_date -> 400 (got {resp.status_code})")

print("\n=== Bulk-assign to multiple learners at once ===")
resp = client.post(
    "/api/instructor/assignments",
    data={"learner_ids": [learner_id, learner2_id], "topic": "B", "topic_type": "letter", "notes": "Class-wide focus this week."},
    headers=instructor_headers,
)
check(resp.status_code == 200, f"bulk-assign -> 200 (got {resp.status_code}: {resp.text[:200]})")
bulk_assignment_ids = []
if resp.status_code == 200:
    bulk_assignments = resp.json()["assignments"]
    check(len(bulk_assignments) == 2, f"bulk-assign created 2 rows (got {len(bulk_assignments)})")
    check({a["learner_id"] for a in bulk_assignments} == {learner_id, learner2_id}, "one row per selected learner")
    bulk_assignment_ids = [a["id"] for a in bulk_assignments]

resp = client.post(
    "/api/instructor/assignments",
    data={"learner_ids": [learner_id, "does-not-exist"], "topic": "B", "topic_type": "letter"},
    headers=instructor_headers,
)
check(resp.status_code == 400, f"bulk-assign with an unknown learner_id -> 400 (got {resp.status_code})")

resp = client.post(
    "/api/instructor/assignments",
    data={"topic": "B", "topic_type": "letter"},
    headers=instructor_headers,
)
check(resp.status_code == 422, f"bulk-assign with no learner_ids at all -> 422 (got {resp.status_code})")

print("\n=== Learner marks an assignment complete / not complete ===")
resp = client.patch(
    f"/api/learner/{learner_id}/assignments/{letter_assignment_id}/complete",
    json={"completed": True},
    headers=learner_headers,
)
check(resp.status_code == 200, f"mark complete -> 200 (got {resp.status_code}: {resp.text[:200]})")
if resp.status_code == 200:
    body = resp.json()
    check(body["completed"] is True and body["completed_at"] is not None, "completed + completed_at set")

resp = client.patch(
    f"/api/learner/{learner_id}/assignments/{letter_assignment_id}/complete",
    json={"completed": False},
    headers=learner_headers,
)
check(resp.status_code == 200 and resp.json()["completed"] is False and resp.json()["completed_at"] is None, "un-completing clears completed_at")

resp = client.patch(
    f"/api/learner/{learner_id}/assignments/{letter_assignment_id}/complete",
    json={"completed": True},
    headers=learner2_headers,
)
check(resp.status_code == 403, f"a different learner cannot complete this assignment -> 403 (got {resp.status_code})")

resp = client.patch(
    f"/api/learner/{learner_id}/assignments/does-not-exist/complete",
    json={"completed": True},
    headers=learner_headers,
)
check(resp.status_code == 404, f"completing an unknown assignment id -> 404 (got {resp.status_code})")

# Leave it completed for the class-analytics count below.
client.patch(f"/api/learner/{learner_id}/assignments/{letter_assignment_id}/complete", json={"completed": True}, headers=learner_headers)

print("\n=== Instructor notes: instructor-only, roster-gated ===")
resp = client.post(
    f"/api/instructor/learners/{learner_id}/notes",
    json={"note": "Great progress on handshapes this week."},
    headers=instructor_headers,
)
check(resp.status_code == 200, f"add note -> 200 (got {resp.status_code}: {resp.text[:200]})")
if resp.status_code == 200:
    check(resp.json()["instructor_name"] == instructor_name, "note carries the instructor's name")

resp = client.get(f"/api/instructor/learners/{learner_id}/notes", headers=instructor_headers)
check(resp.status_code == 200 and len(resp.json()["notes"]) == 1, "note shows up in the listing")

resp = client.post(
    f"/api/instructor/learners/{learner2_id}/notes",
    json={"note": "..."},
    headers=instructor2_headers,
)
check(resp.status_code == 400, f"instructor2 cannot note a learner outside their roster -> 400 (got {resp.status_code})")

resp = client.get(f"/api/learner/{learner_id}/assignments", headers=learner_headers)
check(
    resp.status_code == 200 and all("note" not in a and "notes" != "note" for a in resp.json()["assignments"]),
    "learner-facing assignments payload has no stray 'note' key from the notes feature",
)

print("\n=== Class-wide analytics scoped to the instructor's own roster ===")
resp = client.get("/api/instructor/class-analytics", headers=instructor_headers)
check(resp.status_code == 200, f"class analytics -> 200 (got {resp.status_code}: {resp.text[:200]})")
if resp.status_code == 200:
    stats = resp.json()
    check(stats["learner_count"] == 2, f"learner_count == 2 (got {stats['learner_count']})")
    # 1 (letter A) + 2 (bulk letter B) = 3 total for instructor1's roster; 1 completed.
    check(stats["completed_assignment_count"] == 1, f"completed_assignment_count == 1 (got {stats['completed_assignment_count']})")
    check(stats["outstanding_assignment_count"] == 2, f"outstanding_assignment_count == 2 (got {stats['outstanding_assignment_count']})")

resp = client.get("/api/instructor/class-analytics", headers=instructor2_headers)
check(resp.status_code == 200 and resp.json()["learner_count"] == 0, "instructor2's class analytics reflects their own (empty) roster")

print("\n=== Removing a learner from the roster ===")
resp = client.delete(f"/api/instructor/learners/{learner2_id}", headers=instructor_headers)
check(resp.status_code == 200, f"remove learner -> 200 (got {resp.status_code})")

resp = client.get("/api/instructor/learners", headers=instructor_headers)
check(resp.status_code == 200 and len(resp.json()["learners"]) == 1, "roster now has only 1 learner")

resp = client.post(
    f"/api/instructor/learners/{learner2_id}/assignments",
    data={"topic": "A", "topic_type": "letter"},
    headers=instructor_headers,
)
check(resp.status_code == 400, f"assigning to the removed learner -> 400 again (got {resp.status_code})")

resp = client.delete(f"/api/instructor/learners/{learner2_id}", headers=instructor_headers)
check(resp.status_code == 404, f"removing an already-removed learner -> 404 (got {resp.status_code})")

print("\n=== Invalid assignments / media still rejected as before ===")
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
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "B", "topic_type": "letter"},
    files={"reference_media": ("notes.txt", b"plain text is not an allowed media type", "text/plain")},
    headers=instructor_headers,
)
check(resp.status_code == 400, f"unsupported media content-type -> 400 (got {resp.status_code})")

print("\n=== Learner cannot create assignments or notes (instructor-only) ===")
resp = client.post(
    f"/api/instructor/learners/{learner_id}/assignments",
    data={"topic": "A", "topic_type": "letter"},
    headers=learner_headers,
)
check(resp.status_code == 403, f"learner blocked from creating assignments -> 403 (got {resp.status_code})")

resp = client.post(f"/api/instructor/learners/{learner_id}/notes", json={"note": "x"}, headers=learner_headers)
check(resp.status_code == 403, f"learner blocked from creating notes -> 403 (got {resp.status_code})")

print("\n=== Learner sees their own assignments ===")
resp = client.get(f"/api/learner/{learner_id}/assignments", headers=learner_headers)
check(resp.status_code == 200, f"learner self-view -> 200 (got {resp.status_code})")
if resp.status_code == 200:
    learner_assignments = resp.json()["assignments"]
    check(len(learner_assignments) == 2, f"learner sees both of their assignments (got {len(learner_assignments)})")

print("\n=== Delete an assignment cleans up its media file from disk ===")
if letter_assignment_id and saved_media_path:
    disk_path = UPLOAD_DIR / saved_media_path.rsplit("/", 1)[-1]
    check(disk_path.exists(), f"uploaded file exists on disk before delete ({disk_path})")

    resp = client.delete(f"/api/instructor/assignments/{letter_assignment_id}", headers=instructor_headers)
    check(resp.status_code == 200, f"delete -> 200 (got {resp.status_code})")
    check(not disk_path.exists(), "uploaded file removed from disk after delete")

    resp = client.delete(f"/api/instructor/assignments/{letter_assignment_id}", headers=instructor_headers)
    check(resp.status_code == 404, f"deleting again -> 404 (got {resp.status_code})")

print(f"\n=== {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
