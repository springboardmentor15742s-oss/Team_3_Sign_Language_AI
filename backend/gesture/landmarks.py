"""
Hand & Pose Tracking Engine — Milestone 2.

Wraps MediaPipe Hands (legacy `solutions` API, which bundles its own model
files in the pip package — no internet download needed at runtime, unlike
the newer MediaPipe Tasks API).

Tracked landmarks: 21 points per hand (wrist, thumb x4, index x4, middle x4,
ring x4, pinky x4), matching "Tracked Landmarks" from the project plan
(finger joints, palm/wrist position — full body pose/arm/shoulder tracking
via MediaPipe Pose is a straightforward extension using the same pattern,
left for a later milestone once full-body framing is needed).
"""
import io
from typing import Optional

import numpy as np
from PIL import Image

from mediapipe.python.solutions import hands as mp_hands

# Landmark index -> name, per MediaPipe Hands spec
LANDMARK_NAMES = [
    "WRIST",
    "THUMB_CMC", "THUMB_MCP", "THUMB_IP", "THUMB_TIP",
    "INDEX_MCP", "INDEX_PIP", "INDEX_DIP", "INDEX_TIP",
    "MIDDLE_MCP", "MIDDLE_PIP", "MIDDLE_DIP", "MIDDLE_TIP",
    "RING_MCP", "RING_PIP", "RING_DIP", "RING_TIP",
    "PINKY_MCP", "PINKY_PIP", "PINKY_DIP", "PINKY_TIP",
]

# (start_idx, end_idx) pairs describing the hand "skeleton", useful for the
# frontend to draw connective lines over the landmark points.
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # thumb
    (0, 5), (5, 6), (6, 7), (7, 8),          # index
    (5, 9), (9, 10), (10, 11), (11, 12),     # middle
    (9, 13), (13, 14), (14, 15), (15, 16),   # ring
    (13, 17), (17, 18), (18, 19), (19, 20),  # pinky
    (0, 17),                                  # palm base
]

# A single, process-wide Hands instance (static_image_mode=True is the
# correct mode for independent, unrelated frames such as HTTP-uploaded
# snapshots — it re-runs full detection on every call instead of assuming
# temporal continuity between frames).
_hands = mp_hands.Hands(
    static_image_mode=True,
    max_num_hands=1,
    min_detection_confidence=0.5,
    model_complexity=1,
)


def detect_hand(image_bytes: bytes) -> Optional[dict]:
    """
    Runs hand + landmark detection on a single image.

    Returns None if no hand was detected, otherwise:
        {
            "landmarks": [{"x": float, "y": float, "z": float}, ...] (21 points,
                x/y normalized to [0, 1] relative to image width/height),
            "handedness": "Left" | "Right",
            "handedness_confidence": float,
            "image_width": int,
            "image_height": int,
        }
    """
    with Image.open(io.BytesIO(image_bytes)) as im:
        im = im.convert("RGB")
        width, height = im.size
        rgb_array = np.asarray(im)

    results = _hands.process(rgb_array)

    if not results.multi_hand_landmarks:
        return None

    hand_landmarks = results.multi_hand_landmarks[0]
    landmarks = [{"x": lm.x, "y": lm.y, "z": lm.z} for lm in hand_landmarks.landmark]

    handedness_label = "Unknown"
    handedness_score = 0.0
    if results.multi_handedness:
        classification = results.multi_handedness[0].classification[0]
        handedness_label = classification.label
        handedness_score = classification.score

    return {
        "landmarks": landmarks,
        "handedness": handedness_label,
        "handedness_confidence": handedness_score,
        "image_width": width,
        "image_height": height,
    }
