"""
Live inference + assessment + persistence for the Intermediate
Conversational Fluency word-sign classifier
(data/models/msasl_intermediate_classifier.pkl, trained by
scripts/train_msasl_classifier.py on real MS-ASL clips, 16 words, 49%
test accuracy — see that script's docstring for why 14 lower-data words
were dropped rather than shipped).

Mirrors gesture_recognition_service.py's lazy-bundle-load pattern (a
real trained classifier + predict_proba) and motion_sign_service.py's
recognize/assess/save shape (a sequence of frames in, a pass/fail
attempt out) — this topic sits between the two: a genuinely trained
model like the alphabet classifier, but temporal/sequence input like
motion signs.

Feature extraction reuses holistic_video_landmarks.extract_raw_sequence_from_frames
+ word_landmark_features.normalize_sequence/resample_sequence/
FEATURE_BUILDERS — the EXACT SAME functions train_msasl_classifier.py
used to build the training data, so inference features can never drift
from what the model was trained on.
"""

import uuid
from pathlib import Path

import joblib
import numpy as np
from sqlalchemy.orm import Session

from app.models.word_sign_attempt import WordSignAttempt
from app.services.holistic_video_landmarks import extract_raw_sequence_from_frames
from app.services.word_landmark_features import (
    FEATURE_BUILDERS,
    normalize_sequence,
    resample_sequence,
)

MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "models" / "msasl_intermediate_classifier.pkl"

_bundle: dict | None = None


def _get_bundle() -> dict:
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Word-sign classifier not found: {MODEL_PATH}")
        _bundle = joblib.load(MODEL_PATH)
    return _bundle


def get_supported_word_signs() -> list[str]:
    """The model's own class list — single authoritative source for
    which words this course can currently assess, same reasoning as
    gesture_recognition_service.get_supported_letters."""
    return list(_get_bundle()["classes"])


def get_model_info() -> dict:
    """Honest metadata about the trained model, for anything (course
    catalog, About modal, admin views) that wants to state the model's
    real accuracy rather than imply it's perfect."""
    bundle = _get_bundle()
    return {
        "model_name": bundle.get("model_name"),
        "test_accuracy": bundle.get("test_accuracy"),
        "word_count": len(bundle.get("classes", [])),
        "trained_with_augmentation": bundle.get("trained_with_augmentation"),
    }


def recognize_word_sign(frames: list) -> dict | None:
    """
    Runs the same extraction pipeline used at training time on a short
    sequence of BGR frames (~2-4 seconds of webcam capture, matching the
    frame-count bounds routers/word_signs.py enforces).

    Returns None if no pose/body reference was ever detected across the
    whole sequence (word_landmark_features.normalize_sequence's own
    signal) — the sequence-level "no attempt" case, same semantics as
    motion_sign_service.recognize_motion_sign returning None. Otherwise
    returns {"word": str, "confidence": float, "frame_count": int}.
    """
    raw = extract_raw_sequence_from_frames(frames)
    if raw.shape[0] == 0:
        return None

    normalized = normalize_sequence(raw)
    if normalized is None:
        return None

    bundle = _get_bundle()
    resampled = resample_sequence(normalized, bundle["fixed_frames"])
    build_features = FEATURE_BUILDERS[bundle["feature_set"]]
    features = build_features(resampled[np.newaxis, ...])  # batch of 1

    model = bundle["model"]
    probabilities = model.predict_proba(features)[0]
    best_idx = int(np.argmax(probabilities))
    classes = bundle["classes"]

    return {
        "word": classes[best_idx],
        "confidence": float(probabilities[best_idx]),
        "frame_count": len(frames),
    }


def assess_word_sign(recognition_result: dict | None, target_word: str) -> dict:
    """Compares a recognize_word_sign result against the word the
    learner was asked to sign. Mirrors motion_sign_service.assess_motion_sign
    / sign_assessment_service.assess_sign."""
    if recognition_result is None:
        return {
            "status": "no_attempt_detected",
            "correct": None,
            "confidence": None,
            "target_sign": target_word,
            "predicted_sign": None,
            "frame_count": None,
        }

    predicted_word = recognition_result["word"]
    correct = predicted_word == target_word

    return {
        "status": "pass" if correct else "fail",
        "correct": correct,
        "confidence": recognition_result["confidence"],
        "target_sign": target_word,
        "predicted_sign": predicted_word,
        "frame_count": recognition_result["frame_count"],
    }


def save_word_sign_attempt(db: Session, learner_id: str, assessment_result: dict) -> WordSignAttempt:
    attempt = WordSignAttempt(
        id=str(uuid.uuid4()),
        learner_id=learner_id,
        target_word=assessment_result["target_sign"],
        predicted_word=assessment_result["predicted_sign"],
        status=assessment_result["status"],
        correct=assessment_result["correct"],
        confidence=assessment_result["confidence"],
        frame_count=assessment_result["frame_count"],
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt
