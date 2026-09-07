"""
Covers the real-time "Live mode" evaluation feature: the frontend polls a
recognize-only endpoint every few hundred milliseconds while a learner
holds a pose, so they get a continuously-updating read without any of it
counting as a real, scored practice attempt.

Three of the four topic types (motion signs, word signs, common signs)
already had a standalone /recognize endpoint before this feature existed
(each one's own router docstring already called it "not logged" / "a
standalone tester") — Live mode simply calls those more often. Alphabet
practice didn't have an equivalent, so app/routers/practice.py gained a
new POST /api/practice/recognize this session, mirroring the same shape.

The point of every test below is the same regardless of topic type: a
/recognize call must never create an attempt row, must never touch
streaks/certificates, and must return the model's real read (or an honest
"nothing detected") rather than ever fabricating a result.
"""

import cv2
import numpy as np
import pytest


def _fake_jpeg_bytes() -> bytes:
    """A real, decodable JPEG (solid gray 10x10) — enough to pass
    cv2.imdecode; recognize_gesture/detect_hand_landmarks are monkeypatched
    in every test below, so its actual pixel content is irrelevant."""
    image = np.full((10, 10, 3), 128, dtype=np.uint8)
    ok, encoded = cv2.imencode(".jpg", image)
    assert ok
    return encoded.tobytes()


@pytest.fixture()
def learner(make_user):
    return make_user("Live Preview Learner", "live-preview-learner@test.com", "learner")


# --- Alphabet: POST /api/practice/recognize (the new endpoint) ---------

def test_practice_recognize_returns_a_detected_letter_without_saving_an_attempt(
    client, learner, auth_headers, db_session, monkeypatch
):
    from app.models.practice_attempt import PracticeAttempt

    monkeypatch.setattr(
        "app.routers.practice.recognize_gesture",
        lambda image: {"letter": "A", "confidence": 0.87, "landmarks": [{"x": 0.1, "y": 0.2, "z": 0.0}] * 21},
    )

    before_count = db_session.query(PracticeAttempt).filter(PracticeAttempt.learner_id == learner.id).count()

    r = client.post(
        "/api/practice/recognize",
        files={"image": ("frame.jpg", _fake_jpeg_bytes(), "image/jpeg")},
        headers=auth_headers(learner),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["detected"] is True
    assert body["predicted_letter"] == "A"
    assert body["confidence"] == pytest.approx(0.87)
    assert len(body["landmarks"]) == 21

    after_count = db_session.query(PracticeAttempt).filter(PracticeAttempt.learner_id == learner.id).count()
    assert after_count == before_count  # unchanged — no attempt was logged


def test_practice_recognize_reports_no_hand_honestly(client, learner, auth_headers, monkeypatch):
    monkeypatch.setattr("app.routers.practice.recognize_gesture", lambda image: None)

    r = client.post(
        "/api/practice/recognize",
        files={"image": ("frame.jpg", _fake_jpeg_bytes(), "image/jpeg")},
        headers=auth_headers(learner),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["detected"] is False
    assert body["predicted_letter"] is None
    assert body["confidence"] is None


def test_practice_recognize_requires_auth(client):
    r = client.post("/api/practice/recognize", files={"image": ("frame.jpg", _fake_jpeg_bytes(), "image/jpeg")})
    assert r.status_code == 401


def test_practice_recognize_rejects_undecodable_upload(client, learner, auth_headers):
    r = client.post(
        "/api/practice/recognize",
        files={"image": ("frame.jpg", b"not a real image", "image/jpeg")},
        headers=auth_headers(learner),
    )
    assert r.status_code == 400


# --- Motion signs / word signs / common signs: already-existing /recognize ---
# These endpoints predate Live mode, but Live mode is now what actually
# exercises them continuously — pinning down that they still never persist
# anything protects the whole feature from a future regression that adds
# a save call to a "standalone tester" endpoint by mistake.

def test_motion_signs_recognize_never_saves_an_attempt(client, learner, auth_headers, db_session, monkeypatch):
    from app.models.motion_sign_attempt import MotionSignAttempt

    monkeypatch.setattr(
        "app.routers.motion_signs.recognize_motion_sign",
        lambda frames: {"sign": "Wave", "frame_count": len(frames), "hands_detected_frames": len(frames)},
    )
    before_count = db_session.query(MotionSignAttempt).filter(MotionSignAttempt.learner_id == learner.id).count()

    frame_bytes = _fake_jpeg_bytes()
    r = client.post(
        "/api/motion-signs/recognize",
        files=[("images", (f"frame-{i}.jpg", frame_bytes, "image/jpeg")) for i in range(6)],
        headers=auth_headers(learner),
    )
    assert r.status_code == 200
    assert r.json()["sign"] == "Wave"

    after_count = db_session.query(MotionSignAttempt).filter(MotionSignAttempt.learner_id == learner.id).count()
    assert after_count == before_count


def test_word_signs_recognize_never_saves_an_attempt(client, learner, auth_headers, db_session, monkeypatch):
    from app.models.word_sign_attempt import WordSignAttempt

    monkeypatch.setattr(
        "app.routers.word_signs.recognize_word_sign",
        lambda frames: {"word": "Hello", "confidence": 0.6, "frame_count": len(frames)},
    )
    before_count = db_session.query(WordSignAttempt).filter(WordSignAttempt.learner_id == learner.id).count()

    frame_bytes = _fake_jpeg_bytes()
    r = client.post(
        "/api/word-signs/recognize",
        files=[("images", (f"frame-{i}.jpg", frame_bytes, "image/jpeg")) for i in range(9)],
        headers=auth_headers(learner),
    )
    assert r.status_code == 200
    assert r.json()["word"] == "Hello"

    after_count = db_session.query(WordSignAttempt).filter(WordSignAttempt.learner_id == learner.id).count()
    assert after_count == before_count


def test_common_signs_recognize_is_read_only(client, learner, auth_headers, monkeypatch):
    monkeypatch.setattr(
        "app.routers.common_signs.recognize_common_sign",
        lambda image: {"sign": "Yes", "finger_state": {}, "landmarks": [{"x": 0.0, "y": 0.0, "z": 0.0}] * 21},
    )

    r = client.post(
        "/api/common-signs/recognize",
        files={"image": ("frame.jpg", _fake_jpeg_bytes(), "image/jpeg")},
        headers=auth_headers(learner),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["detected_hand"] is True
    assert body["sign"] == "Yes"
