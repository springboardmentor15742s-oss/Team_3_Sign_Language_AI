"""
End-to-end check of the new word-signs feature: registers a learner,
hits /api/word-signs/supported, confirms the course catalog now shows
conversational-fluency as built with real metadata, then feeds a real
leftover MS-ASL test clip (from /tmp/batch2_extract, a prior extraction
batch's test-split videos) through /api/word-signs/feedback via ffmpeg
frame extraction, to prove the whole path (frame upload -> landmark
extraction -> classifier -> assessment -> attempt saved -> tiered
feedback) works end to end on a REAL clip, not just synthetic blanks.

Note: /tmp/batch2_extract only exists in the environment this feature
was originally built and validated in — if it's not present here, this
script falls back to a synthetic all-black frame sequence, which still
proves the no_attempt_detected path works, just not the real-prediction
path. Re-download a few MS-ASL test clips locally to exercise that path
here too.

Run from backend/:
    python3 scripts/test_word_signs_integration.py
"""
import csv
import glob
import io
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, ".")

from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import learning_activity, motion_sign_attempt, practice_attempt, word_sign_attempt  # noqa: F401
from app.models.user import User
from app.services.auth_service import create_access_token, hash_password

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


print("=== Create/reuse a test learner (same pattern as test_integration_workflow.py) ===")
db = SessionLocal()
email = "wordsign-test@test.com"
learner = db.query(User).filter(User.email == email).first()
if learner is None:
    learner = User(
        id="wordsign-test-learner",
        name="Word Sign Tester",
        email=email,
        hashed_password=hash_password("test-password"),
        role="learner",
    )
    db.add(learner)
    db.commit()
    db.refresh(learner)
from app.models.word_sign_attempt import WordSignAttempt
db.query(WordSignAttempt).filter(WordSignAttempt.learner_id == learner.id).delete()
db.commit()
learner_id = learner.id
headers = {"Authorization": f"Bearer {create_access_token({'sub': learner.id})}"}

print("\n=== /api/word-signs/supported ===")
supported = client.get("/api/word-signs/supported", headers=headers)
check(supported.status_code == 200, "supported status 200")
sdata = supported.json()
check(len(sdata["words"]) == 16, f"16 supported words (got {len(sdata['words'])})")
check(sdata["model_test_accuracy"] is not None and 0.4 < sdata["model_test_accuracy"] < 0.6,
      f"model_test_accuracy in a sane 40-60% range (got {sdata['model_test_accuracy']})")
print("  words:", sdata["words"])
print("  model_test_accuracy:", sdata["model_test_accuracy"])

print("\n=== /api/learner/{id}/courses reflects the new course ===")
courses = client.get(f"/api/learner/{learner_id}/courses", headers=headers)
check(courses.status_code == 200, "courses status 200")
cf = next(c for c in courses.json()["courses"] if c["id"] == "conversational-fluency")
check(cf["built"] is True, "conversational-fluency built=True")
check(cf["route"] == "/conversational-fluency", f"route set (got {cf['route']})")
check(cf["item_count"] == 16, f"item_count=16 (got {cf['item_count']})")
check(cf["progress_percent"] == 0.0, f"progress_percent starts at 0 (got {cf['progress_percent']})")
check(cf["model_test_accuracy"] is not None, "model_test_accuracy surfaced on course entry")
wc = next(c for c in courses.json()["courses"] if c["id"] == "workplace-communication")
check(wc["built"] is False, "workplace-communication still built=False")
print("  conversational-fluency entry:", cf)

print("\n=== Real-clip recognition + feedback (no attempt yet expected to be graceful either way) ===")
manifest_path = Path("/tmp/batch2_extract/intermediate_clips_manifest.csv")
test_clip_dir = Path("/tmp/batch2_extract/test")
target_word = None
clip_path = None
if manifest_path.exists():
    with open(manifest_path, newline="") as f:
        rows = list(csv.DictReader(f))
    for row in rows:
        gloss = (row.get("gloss") or "").strip().lower()
        clip_id = row.get("clip_id", "")
        if gloss in sdata["words"]:
            candidate = test_clip_dir / f"{clip_id}.mp4"
            if candidate.exists():
                clip_path = candidate
                target_word = gloss
                break

if clip_path is None:
    print("  (skipped: couldn't find a leftover test clip whose label is in the 16-word vocab —"
          " falling back to a synthetic all-black frame sequence instead)")
    import numpy as np
    import cv2
    frames = [np.zeros((240, 320, 3), dtype="uint8") for _ in range(15)]
    files = []
    for i, frame in enumerate(frames):
        ok, buf = cv2.imencode(".jpg", frame)
        files.append(("images", (f"frame-{i}.jpg", io.BytesIO(buf.tobytes()), "image/jpeg")))
    target_word = sdata["words"][0]
    resp = client.post(
        "/api/word-signs/feedback",
        data={"target_word": target_word},
        files=files,
        headers=headers,
    )
    check(resp.status_code == 200, f"feedback status 200 (got {resp.status_code}: {resp.text[:200]})")
    rdata = resp.json()
    check(rdata["status"] == "no_attempt_detected", f"blank frames -> no_attempt_detected (got {rdata['status']})")
    check(rdata["attempt_id"] is None, "no attempt saved for no_attempt_detected")
else:
    print(f"  Using real clip: {clip_path.name}  target word: {target_word}")
    with tempfile.TemporaryDirectory() as tmpdir:
        out_pattern = f"{tmpdir}/frame_%03d.jpg"
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(clip_path), "-vf", "fps=8", out_pattern],
            check=True, capture_output=True,
        )
        frame_files = sorted(Path(tmpdir).glob("frame_*.jpg"))
        check(8 <= len(frame_files) <= 90, f"extracted {len(frame_files)} frames (within router bounds)")
        files = [("images", (fp.name, open(fp, "rb"), "image/jpeg")) for fp in frame_files]
        resp = client.post(
            "/api/word-signs/feedback",
            data={"target_word": target_word},
            files=files,
            headers=headers,
        )
        for _, (_, fh, _) in files:
            fh.close()
    check(resp.status_code == 200, f"feedback status 200 (got {resp.status_code}: {resp.text[:300]})")
    rdata = resp.json()
    print("  result:", rdata)
    check(rdata["status"] in ("pass", "fail"), f"real clip scored pass/fail, not no_attempt_detected (got {rdata['status']})")
    check(rdata["attempt_id"] is not None, "attempt saved")
    check(rdata["confidence"] is not None, "confidence populated from real predict_proba")
    check(rdata["learner_level"] is not None, "tiered feedback learner_level present")
    check(rdata["feedback"], "feedback message present")

print("\n=== Course progress updates after a scored attempt ===")
courses2 = client.get(f"/api/learner/{learner_id}/courses", headers=headers)
cf2 = next(c for c in courses2.json()["courses"] if c["id"] == "conversational-fluency")
print("  progress after attempt:", cf2["progress_percent"])
if clip_path is not None:
    check(cf2["progress_percent"] is not None and cf2["progress_percent"] > 0,
          f"progress_percent > 0 after a scored real attempt (got {cf2['progress_percent']})")

print(f"\n=== {PASS} passed, {FAIL} failed ===")
sys.exit(1 if FAIL else 0)
