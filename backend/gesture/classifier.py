"""
Gesture Recognition Engine — Milestone 2.

Classifies a detected hand's pose into one of the gestures in
`reference_signs.GESTURE_LIBRARY` using a geometric, finger-state heuristic
computed from MediaPipe's 21 hand landmarks (no training data required).

See reference_signs.py for the rationale and the Milestone 3+ upgrade path
to a trained CNN/LSTM model using the datasets integrated in Milestone 1.
"""
import math

from gesture.reference_signs import GESTURE_LIBRARY, FINGER_NAMES

# Landmark indices (MediaPipe Hands)
WRIST = 0
THUMB_MCP, THUMB_IP, THUMB_TIP = 2, 3, 4
INDEX_MCP, INDEX_PIP, INDEX_TIP = 5, 6, 8
MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP = 9, 10, 12
RING_MCP, RING_PIP, RING_TIP = 13, 14, 16
PINKY_MCP, PINKY_PIP, PINKY_TIP = 17, 18, 20


def _dist(a, b):
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2)


def get_finger_states(landmarks: list) -> list:
    """
    Returns [thumb, index, middle, ring, pinky] as 0/1 (curled/extended),
    derived purely from landmark geometry.

    Non-thumb fingers: extended if the fingertip is farther from the palm
    base (wrist) than the corresponding PIP joint — robust to hand
    rotation/tilt, unlike a plain "tip.y < pip.y" check.

    Thumb: extended if the tip is meaningfully farther from the palm
    (pinky MCP) than the thumb's own MCP joint is — this avoids needing to
    know left/right handedness (thumbs move sideways, not up/down).
    """
    wrist = landmarks[WRIST]
    pinky_mcp = landmarks[PINKY_MCP]

    def finger_extended(mcp_idx, pip_idx, tip_idx):
        tip_to_wrist = _dist(landmarks[tip_idx], wrist)
        pip_to_wrist = _dist(landmarks[pip_idx], wrist)
        return 1 if tip_to_wrist > pip_to_wrist * 1.05 else 0

    thumb_tip_to_palm = _dist(landmarks[THUMB_TIP], pinky_mcp)
    thumb_mcp_to_palm = _dist(landmarks[THUMB_MCP], pinky_mcp)
    thumb_extended = 1 if thumb_tip_to_palm > thumb_mcp_to_palm * 1.15 else 0

    return [
        thumb_extended,
        finger_extended(INDEX_MCP, INDEX_PIP, INDEX_TIP),
        finger_extended(MIDDLE_MCP, MIDDLE_PIP, MIDDLE_TIP),
        finger_extended(RING_MCP, RING_PIP, RING_TIP),
        finger_extended(PINKY_MCP, PINKY_PIP, PINKY_TIP),
    ]


def classify_by_fingerstate(finger_state: list):
    """
    Matches a finger-state vector against the gesture library using Hamming
    distance. Returns (best_label, confidence, all_scores).
    """
    scores = {}
    for label, info in GESTURE_LIBRARY.items():
        pattern = info["pattern"]
        matches = sum(1 for a, b in zip(finger_state, pattern) if a == b)
        scores[label] = matches / len(pattern)  # 0..1

    best_label = max(scores, key=scores.get)
    best_confidence = scores[best_label]

    # If nothing matches well, report as unrecognized rather than forcing a guess.
    if best_confidence < 0.6:
        return None, best_confidence, scores

    return best_label, best_confidence, scores


def describe_finger_state(finger_state: list) -> list:
    """Human-readable [{'finger': 'Thumb', 'extended': True}, ...] for the UI."""
    return [
        {"finger": name, "extended": bool(state)}
        for name, state in zip(FINGER_NAMES, finger_state)
    ]
