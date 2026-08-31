from pathlib import Path

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions
from mediapipe.tasks.python.vision import HandLandmarker, HandLandmarkerOptions, RunningMode

# Path to the downloaded MediaPipe Hand Landmarker model, relative to the backend folder
MODEL_PATH = Path(__file__).resolve().parent.parent.parent / "data" / "models" / "hand_landmarker.task"

WRIST_IDX = 0
MIDDLE_MCP_IDX = 9  # stable reference point for hand scale, regardless of pose

_landmarker: HandLandmarker | None = None


def _get_landmarker() -> HandLandmarker:
    """
    Lazily creates a single shared HandLandmarker instance so the model
    is only loaded into memory once per process.
    """
    global _landmarker
    if _landmarker is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Hand landmarker model not found: {MODEL_PATH}")

        options = HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
            running_mode=RunningMode.IMAGE,
            num_hands=2,
            min_hand_detection_confidence=0.5,
        )
        _landmarker = HandLandmarker.create_from_options(options)

    return _landmarker


def detect_hand_landmarks(image: np.ndarray) -> list[dict]:
    """
    Runs MediaPipe Hand Landmarker on a BGR image (as read by OpenCV, or a
    single video frame) and returns one entry per detected hand, each with
    its handedness and 21 normalized {x, y, z} landmarks.
    """
    landmarker = _get_landmarker()

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_image)

    result = landmarker.detect(mp_image)

    hands = []
    for hand_landmarks, handedness in zip(result.hand_landmarks, result.handedness):
        hands.append({
            "handedness": handedness[0].category_name,
            "confidence": handedness[0].score,
            "landmarks": [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in hand_landmarks],
        })

    return hands


def detect_hand_landmarks_from_path(image_path: str) -> list[dict]:
    """
    Loads an image from disk and runs detect_hand_landmarks on it.
    """
    image = cv2.imread(image_path)
    if image is None:
        raise FileNotFoundError(f"Could not read image: {image_path}")

    return detect_hand_landmarks(image)


def normalize_landmarks(landmarks: list[dict]) -> list[float]:
    """
    Makes landmarks translation- and scale-invariant so a downstream
    classifier generalizes regardless of where the hand sits in frame or
    how large it appears:
      - Subtract the wrist (landmark 0) position from every point.
      - Divide by the wrist-to-middle-MCP (landmark 9) distance, a
        stable proxy for hand size across poses.

    Used identically at training time (prepare_gesture_dataset.py) and
    inference time (gesture_recognition_service.py) so features never
    drift between the two.
    """
    wrist = landmarks[WRIST_IDX]
    ref = landmarks[MIDDLE_MCP_IDX]

    scale = (
        (ref["x"] - wrist["x"]) ** 2
        + (ref["y"] - wrist["y"]) ** 2
        + (ref["z"] - wrist["z"]) ** 2
    ) ** 0.5
    if scale < 1e-6:
        scale = 1e-6

    features = []
    for lm in landmarks:
        features.append((lm["x"] - wrist["x"]) / scale)
        features.append((lm["y"] - wrist["y"]) / scale)
        features.append((lm["z"] - wrist["z"]) / scale)

    return features
