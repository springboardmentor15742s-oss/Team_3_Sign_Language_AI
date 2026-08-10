from pathlib import Path

import cv2
import joblib
import numpy as np

from app.services.hand_tracking_service import detect_hand_landmarks, normalize_landmarks

# Path to the trained gesture classifier, relative to the backend folder
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "models" / "gesture_classifier.pkl"

_bundle: dict | None = None


def _get_bundle() -> dict:
    """
    Lazily loads the trained model bundle (model + class list) so it's
    only read from disk once per process.
    """
    global _bundle
    if _bundle is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Gesture classifier not found: {MODEL_PATH}")
        _bundle = joblib.load(MODEL_PATH)

    return _bundle


def recognize_gesture(image: np.ndarray) -> dict | None:
    """
    Runs hand tracking on a BGR image (as read by OpenCV, or a single
    video frame), normalizes the landmarks the same way training data
    was prepared, and predicts the gesture letter.

    Returns None if no hand is detected in the frame — callers should
    treat that as an upstream "no hand present" case, not a prediction.
    Otherwise returns {"letter": str, "confidence": float}.
    """
    hands = detect_hand_landmarks(image)
    if not hands:
        return None

    best_hand = max(hands, key=lambda h: h["confidence"])
    features = normalize_landmarks(best_hand["landmarks"])

    model = _get_bundle()["model"]

    probabilities = model.predict_proba([features])[0]
    best_idx = int(np.argmax(probabilities))

    return {
        "letter": model.classes_[best_idx],
        "confidence": float(probabilities[best_idx]),
    }


def recognize_gesture_from_path(image_path: str) -> dict | None:
    """
    Loads an image from disk and runs recognize_gesture on it.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    return recognize_gesture(image)


def get_supported_letters() -> list[str]:
    """
    Returns the gesture classes the trained classifier can recognize —
    the model's own class list, so callers (e.g. recommendation_service)
    have a single authoritative source for which letters are
    practiceable instead of a separately maintained alphabet list.
    """
    model = _get_bundle()["model"]
    return list(model.classes_)
