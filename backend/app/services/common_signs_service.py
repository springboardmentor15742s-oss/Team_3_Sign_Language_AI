"""
Rule-based recognizer for a small set of common ASL signs that are
genuinely representable as a single static handshape — unlike the trained
gesture_classifier (alphabet), this is NOT a trained model. It's explicit
landmark geometry (finger-extended tests) run against the same MediaPipe
hand landmarks the alphabet classifier uses.

Why rule-based instead of trained: the platform's dataset is static ASL
alphabet images only. Most common conversational signs (Hello, Thank You,
Please, Help) are motion-based or two-handed in real ASL and cannot be
honestly represented as a single static frame — see SECURITY.md / the
About modal for the same scoping decision applied to the alphabet model.
The three signs below were chosen specifically because they ARE real,
static, single-hand handshapes:

  - "I Love You" (ILY handshape): thumb, index, and pinky extended;
    middle and ring folded. A standard ASL emblem sign, not a
    simplification of anything else.
  - "Yes": approximated as a closed fist (all four fingers folded). The
    real sign is a fist bobbing at the wrist like a nodding head — the
    static frame here captures the handshape, not the motion.
  - "No": approximated as index + middle extended together with the
    thumb pulled in close to their tips ("flat O" pinch). The real sign
    opens and closes that pinch; this captures one static frame of it.
    This is the least validated of the three (no labeled test images
    were available) — tune the pinch threshold below against real
    captures if it misfires.

Finger-extended geometry was verified against real labeled images from
the existing ASL alphabet dataset (e.g. letter Y — thumb+pinky extended —
is correctly distinguished from "I Love You" — thumb+index+pinky — by
whether the index finger tests as extended).
"""

import math

from app.services.hand_tracking_service import detect_hand_landmarks

WRIST = 0
THUMB_TIP, THUMB_IP = 4, 3
INDEX_TIP, INDEX_PIP, INDEX_MCP = 8, 6, 5
MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP = 12, 10, 9
RING_TIP, RING_PIP, RING_MCP = 16, 14, 13
PINKY_TIP, PINKY_PIP, PINKY_MCP = 20, 18, 17

# thumb-to-index-tip distance (relative to hand scale) below which the
# thumb counts as "pinched in" against the index finger, for the "No" test
NO_PINCH_RATIO_THRESHOLD = 0.6

SUPPORTED_SIGNS = ["I Love You", "Yes", "No"]


def _dist(a: dict, b: dict) -> float:
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2 + (a["z"] - b["z"]) ** 2)


def _finger_extended(landmarks: list[dict], tip: int, pip: int, mcp: int) -> bool:
    """
    A finger counts as extended when its joints are monotonically farther
    from the wrist going tip -> pip -> mcp — i.e. the finger is straight
    and pointing away from the palm, rather than curled into it.
    """
    wrist = landmarks[WRIST]
    d_tip = _dist(wrist, landmarks[tip])
    d_pip = _dist(wrist, landmarks[pip])
    d_mcp = _dist(wrist, landmarks[mcp])
    return d_tip > d_pip > d_mcp


def _thumb_extended(landmarks: list[dict]) -> bool:
    """
    The thumb moves sideways rather than along the wrist axis, so it gets
    its own test: extended when the tip is farther from the index MCP
    (the base of the index finger) than the thumb's own IP joint is.
    """
    return _dist(landmarks[THUMB_TIP], landmarks[INDEX_MCP]) > _dist(
        landmarks[THUMB_IP], landmarks[INDEX_MCP]
    )


def _finger_state(landmarks: list[dict]) -> dict[str, bool]:
    return {
        "thumb": _thumb_extended(landmarks),
        "index": _finger_extended(landmarks, INDEX_TIP, INDEX_PIP, INDEX_MCP),
        "middle": _finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP),
        "ring": _finger_extended(landmarks, RING_TIP, RING_PIP, RING_MCP),
        "pinky": _finger_extended(landmarks, PINKY_TIP, PINKY_PIP, PINKY_MCP),
    }


def _classify(state: dict[str, bool], landmarks: list[dict]) -> str | None:
    if state["thumb"] and state["index"] and state["pinky"] and not state["middle"] and not state["ring"]:
        return "I Love You"

    if not state["index"] and not state["middle"] and not state["ring"] and not state["pinky"]:
        return "Yes"

    if state["index"] and state["middle"] and not state["ring"] and not state["pinky"]:
        wrist_scale = _dist(landmarks[WRIST], landmarks[MIDDLE_MCP])
        if wrist_scale > 1e-6:
            pinch_ratio = _dist(landmarks[THUMB_TIP], landmarks[INDEX_TIP]) / wrist_scale
            if pinch_ratio < NO_PINCH_RATIO_THRESHOLD:
                return "No"

    return None


def recognize_common_sign(image) -> dict | None:
    """
    Runs hand detection on a BGR image and classifies it against
    SUPPORTED_SIGNS using landmark geometry.

    Returns None if no hand is detected (same "no attempt" semantics as
    gesture_recognition_service.recognize_gesture). Otherwise returns
    {"sign": str | None, "finger_state": dict, "landmarks": list[dict]} —
    sign is None when a hand was found but it didn't match any of the
    three supported shapes.
    """
    hands = detect_hand_landmarks(image)
    if not hands:
        return None

    best_hand = max(hands, key=lambda h: h["confidence"])
    landmarks = best_hand["landmarks"]
    state = _finger_state(landmarks)
    sign = _classify(state, landmarks)

    return {
        "sign": sign,
        "finger_state": state,
        "landmarks": landmarks,
    }
