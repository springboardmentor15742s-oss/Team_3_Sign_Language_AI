"""
Rule-based recognizer for everyday motion gestures — Wave and Clap — run
against a short sequence of frames (not a single image, unlike the
alphabet classifier and common_signs_service). This is the platform's
first genuinely *motion*-based recognizer, and it's rule-based for the
same reason common_signs_service is: there is no trained temporal model
on this platform yet, and no video-sequence dataset has been downloaded
(see the "Intermediate Conversational Fluency" / "Professional &
Workplace Communication" course entries, which stay honestly locked for
exactly that reason). Wave and Clap are here instead of there because
they're generic body-language gestures, not ASL vocabulary signs — and
because their motion is simple enough to detect correctly from hand
trajectory alone, without needing a trained model or any labeled dataset.

Why not Handshake too: a handshake is inherently a two-person motion. A
single learner alone at a webcam can only mime an empty-air "grip and
shake," which has no reliable, unambiguous hand-trajectory signature to
rule-test against (unlike an open palm oscillating side to side, or two
hands meeting and separating) — building a rule for it now would mean
guessing at a threshold with no real footage to validate it against, the
same trap the "No" sign's docstring in common_signs_service flags. Left
out until there's real captured video to check a rule against, rather
than shipped as an unvalidated guess.

Both detectors work on the SAME per-frame hand landmarks used everywhere
else (hand_tracking_service.detect_hand_landmarks) — the only new part is
looking at how those landmarks move across a sequence of frames instead
of classifying one frame in isolation.
"""

import math
import uuid

from sqlalchemy.orm import Session

from app.models.motion_sign_attempt import MotionSignAttempt
from app.services.hand_tracking_service import detect_hand_landmarks

WRIST = 0
INDEX_TIP, INDEX_PIP, INDEX_MCP = 8, 6, 5
MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP = 12, 10, 9
RING_TIP, RING_PIP, RING_MCP = 16, 14, 13
PINKY_TIP, PINKY_PIP, PINKY_MCP = 20, 18, 17

SUPPORTED_MOTION_SIGNS = ["Wave", "Clap"]

# A frame sequence needs hands detected in at least this fraction of its
# frames to be scored at all — otherwise it's "no_attempt_detected", the
# same semantics as a single frame with no hand found elsewhere in the app.
MIN_DETECTION_RATIO = 0.5

# Wave: minimum number of left-right direction reversals in wrist x
# position to count as "waving" rather than an incidental hand drift.
WAVE_MIN_REVERSALS = 2
# Wave: minimum swing width (normalized by hand scale) a reversal must
# span to count — filters out small jitter being mistaken for a wave.
WAVE_MIN_AMPLITUDE = 0.35

# Clap: two hands must come at least this close (normalized by hand
# scale) at some point in the sequence to count as contact.
CLAP_MAX_CONTACT_DISTANCE = 0.6
# Clap: hands must also have been at least this far apart before AND
# after the closest point — otherwise it's just two hands resting near
# each other, not an approach-contact-separate motion.
CLAP_MIN_SEPARATION = 1.3


def _dist(a: dict, b: dict) -> float:
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2 + (a["z"] - b["z"]) ** 2)


def _hand_scale(landmarks: list[dict]) -> float:
    """Wrist-to-middle-MCP distance, the same stable size reference used
    for normalization elsewhere (hand_tracking_service.normalize_landmarks)."""
    scale = _dist(landmarks[WRIST], landmarks[MIDDLE_MCP])
    return scale if scale > 1e-6 else 1e-6


def _finger_extended(landmarks: list[dict], tip: int, pip: int, mcp: int) -> bool:
    wrist = landmarks[WRIST]
    d_tip = _dist(wrist, landmarks[tip])
    d_pip = _dist(wrist, landmarks[pip])
    d_mcp = _dist(wrist, landmarks[mcp])
    return d_tip > d_pip > d_mcp


def _is_open_palm(landmarks: list[dict]) -> bool:
    """At least 3 of the 4 non-thumb fingers extended — an open, waving
    hand, as opposed to a fist or a pinch."""
    fingers = [
        _finger_extended(landmarks, INDEX_TIP, INDEX_PIP, INDEX_MCP),
        _finger_extended(landmarks, MIDDLE_TIP, MIDDLE_PIP, MIDDLE_MCP),
        _finger_extended(landmarks, RING_TIP, RING_PIP, RING_MCP),
        _finger_extended(landmarks, PINKY_TIP, PINKY_PIP, PINKY_MCP),
    ]
    return sum(fingers) >= 3


def _detect_wave(single_hand_frames: list[list[dict]]) -> bool:
    """
    A wave is an open palm whose wrist x-position swings back and forth
    at least WAVE_MIN_REVERSALS times, each swing wide enough
    (WAVE_MIN_AMPLITUDE, in hand-scale units) to not just be jitter.

    Standard zigzag/peak-trough detection: track a running extreme in the
    current direction of travel, and count a reversal each time motion
    turns back against that extreme by at least the amplitude threshold.
    """
    open_frames = [lm for lm in single_hand_frames if _is_open_palm(lm)]
    if len(open_frames) < len(single_hand_frames) * MIN_DETECTION_RATIO:
        return False
    if len(single_hand_frames) < 3:
        return False

    # Normalized x position per frame (hand scale varies a little frame
    # to frame as the hand moves toward/away from camera; use each
    # frame's own scale so amplitude stays a fair comparison throughout).
    xs = [lm[WRIST]["x"] / _hand_scale(lm) for lm in single_hand_frames]

    reversals = 0
    pivot = xs[0]     # last confirmed reversal point (or the start)
    extreme = xs[0]   # running max/min since the pivot
    direction = 0     # 0 = undetermined yet, 1 = rising, -1 = falling

    for x in xs[1:]:
        if direction >= 0 and x >= extreme:
            extreme = x
            direction = 1
        elif direction <= 0 and x <= extreme:
            extreme = x
            direction = -1
        else:
            # Motion turned back against the running extreme.
            swing = abs(extreme - pivot)
            if swing >= WAVE_MIN_AMPLITUDE:
                reversals += 1
                pivot = extreme
            extreme = x
            direction = -1 if direction == 1 else 1

    return reversals >= WAVE_MIN_REVERSALS


def _detect_clap(two_hand_frames: list[tuple[list[dict], list[dict]]]) -> bool:
    """
    A clap is two hands whose wrist-to-wrist distance (normalized by
    average hand scale) comes together to within CLAP_MAX_CONTACT_DISTANCE
    at some point, while also being at least CLAP_MIN_SEPARATION apart
    both before and after that point — i.e. approach, contact, separate,
    not just two hands sitting near each other the whole time.
    """
    distances = []
    for hand_a, hand_b in two_hand_frames:
        scale = (_hand_scale(hand_a) + _hand_scale(hand_b)) / 2
        distances.append(_dist(hand_a[WRIST], hand_b[WRIST]) / scale)

    if not distances:
        return False

    min_idx = min(range(len(distances)), key=lambda i: distances[i])
    if distances[min_idx] > CLAP_MAX_CONTACT_DISTANCE:
        return False

    before = distances[:min_idx]
    after = distances[min_idx + 1:]
    had_separation_before = any(d >= CLAP_MIN_SEPARATION for d in before) if before else False
    had_separation_after = any(d >= CLAP_MIN_SEPARATION for d in after) if after else False

    # A clap right at the start or end of the clip only needs separation
    # on the side that exists — the learner may start already mid-motion.
    if not before:
        return had_separation_after
    if not after:
        return had_separation_before
    return had_separation_before and had_separation_after


def recognize_motion_sign(frames: list) -> dict | None:
    """
    Runs hand detection on each frame of a short sequence (list of BGR
    images, ~2-3 seconds of webcam capture) and checks it against
    SUPPORTED_MOTION_SIGNS.

    Returns None if hands weren't detected in enough frames to judge
    motion at all (MIN_DETECTION_RATIO) — the sequence-level equivalent
    of "no hand detected" elsewhere in the app. Otherwise returns
    {"sign": str | None, "frame_count": int, "hands_detected_frames": int}
    — sign is None when hands were tracked but didn't match Wave or Clap.
    """
    per_frame_hands = [detect_hand_landmarks(frame) for frame in frames]
    detected_frames = [hands for hands in per_frame_hands if hands]

    if len(detected_frames) < len(frames) * MIN_DETECTION_RATIO:
        return None

    single_hand_frames = [hands[0]["landmarks"] for hands in detected_frames if len(hands) == 1]
    two_hand_sequences = [
        (hands[0]["landmarks"], hands[1]["landmarks"])
        for hands in detected_frames
        if len(hands) >= 2
    ]

    sign = None
    if len(two_hand_sequences) >= len(frames) * MIN_DETECTION_RATIO and _detect_clap(two_hand_sequences):
        sign = "Clap"
    elif len(single_hand_frames) >= len(frames) * MIN_DETECTION_RATIO and _detect_wave(single_hand_frames):
        sign = "Wave"

    return {
        "sign": sign,
        "frame_count": len(frames),
        "hands_detected_frames": len(detected_frames),
    }


def assess_motion_sign(motion_result: dict | None, target_sign: str) -> dict:
    """
    Compares a recognize_motion_sign result against the motion sign the
    learner was asked to perform. Mirrors sign_assessment_service.assess_sign
    for the static alphabet — same no_attempt_detected vs. pass/fail split.
    """
    if motion_result is None:
        return {
            "status": "no_attempt_detected",
            "correct": None,
            "target_sign": target_sign,
            "predicted_sign": None,
            "frame_count": None,
            "hands_detected_frames": None,
        }

    predicted_sign = motion_result["sign"]
    correct = predicted_sign == target_sign

    return {
        "status": "pass" if correct else "fail",
        "correct": correct,
        "target_sign": target_sign,
        "predicted_sign": predicted_sign,
        "frame_count": motion_result["frame_count"],
        "hands_detected_frames": motion_result["hands_detected_frames"],
    }


def save_motion_sign_attempt(db: Session, learner_id: str, assessment_result: dict) -> MotionSignAttempt:
    """Persists an assess_motion_sign result as a MotionSignAttempt row."""
    attempt = MotionSignAttempt(
        id=str(uuid.uuid4()),
        learner_id=learner_id,
        target_sign=assessment_result["target_sign"],
        predicted_sign=assessment_result["predicted_sign"],
        status=assessment_result["status"],
        correct=assessment_result["correct"],
        confidence=None,  # rule-based match — see MotionSignAttempt.confidence docstring
        frame_count=assessment_result["frame_count"],
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt
