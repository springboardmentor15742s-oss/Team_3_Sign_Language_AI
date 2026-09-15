"""
Sign Accuracy Assessment Engine — Milestone 2.

Given a target gesture and a detected hand, scores how closely the
detected hand shape matches the target, and generates mistake-level
feedback (a lightweight preview of Milestone 3's full AI Feedback engine).

Assessment metrics implemented (per the project plan's "Assessment Metrics"
list): Hand Shape Accuracy, Position Accuracy, Overall Sign Accuracy.
(Motion Accuracy / Gesture Timing require video sequences, not a single
static frame — those land in a future milestone once continuous-video
capture is added.)
"""
from gesture.classifier import get_finger_states, describe_finger_state
from gesture.reference_signs import GESTURE_LIBRARY, FINGER_NAMES


def _position_accuracy(landmarks: list) -> float:
    """
    Rough proxy for 'is the hand reasonably centered and fully in frame'.
    Penalizes hands that are clipped at the edges or very small/off-center.
    Returns a 0..100 score.
    """
    xs = [lm["x"] for lm in landmarks]
    ys = [lm["y"] for lm in landmarks]
    min_x, max_x, min_y, max_y = min(xs), max(xs), min(ys), max(ys)

    # Penalize hands touching/crossing the frame edges (likely clipped).
    edge_margin = 0.03
    clipped = min_x < edge_margin or min_y < edge_margin or max_x > 1 - edge_margin or max_y > 1 - edge_margin
    edge_score = 70 if clipped else 100

    # Reward a hand that's reasonably large in frame (not tiny/far away).
    hand_span = max(max_x - min_x, max_y - min_y)
    size_score = min(100, max(40, hand_span * 220))

    return round((edge_score + size_score) / 2, 1)


def assess_gesture(landmarks: list, target_label: str, handedness_confidence: float) -> dict:
    """
    Returns a full assessment dict:
        {
            "target_label": str,
            "detected_finger_state": [...],
            "expected_finger_state": [...],
            "hand_shape_accuracy": float (0-100),
            "position_accuracy": float (0-100),
            "overall_accuracy": float (0-100),
            "matched": bool,
            "feedback": [str, ...],
            "finger_breakdown": [{"finger": ..., "expected": bool, "actual": bool, "correct": bool}, ...],
        }
    """
    reference = GESTURE_LIBRARY.get(target_label)
    if reference is None:
        raise ValueError(f"Unknown target gesture: {target_label}")

    expected_pattern = reference["pattern"]
    detected_state = get_finger_states(landmarks)

    correct_fingers = sum(1 for a, b in zip(detected_state, expected_pattern) if a == b)
    hand_shape_accuracy = round((correct_fingers / len(expected_pattern)) * 100, 1)

    position_accuracy = _position_accuracy(landmarks)

    # Overall score: hand shape is the primary signal for a static-image
    # assessment; detection confidence and framing contribute the rest.
    overall_accuracy = round(
        hand_shape_accuracy * 0.7 + position_accuracy * 0.15 + (handedness_confidence * 100) * 0.15,
        1,
    )

    matched = correct_fingers == len(expected_pattern)

    finger_breakdown = []
    feedback = []
    for name, expected, actual in zip(FINGER_NAMES, expected_pattern, detected_state):
        correct = expected == actual
        finger_breakdown.append(
            {"finger": name, "expected": bool(expected), "actual": bool(actual), "correct": correct}
        )
        if not correct:
            if expected == 1 and actual == 0:
                feedback.append(f"Extend your {name.lower()} finger further.")
            else:
                feedback.append(f"Curl your {name.lower()} finger into your palm.")

    if matched:
        feedback.insert(0, "Great job! Your hand shape matches the target sign.")
    elif not feedback:
        feedback.append("Hand shape mostly correct — fine-tune your finger positions.")

    if position_accuracy < 80:
        feedback.append("Try centering your hand fully in frame, a bit closer to the camera.")

    return {
        "target_label": target_label,
        "detected_finger_state": describe_finger_state(detected_state),
        "expected_finger_state": describe_finger_state(expected_pattern),
        "hand_shape_accuracy": hand_shape_accuracy,
        "position_accuracy": position_accuracy,
        "overall_accuracy": overall_accuracy,
        "matched": matched,
        "feedback": feedback,
        "finger_breakdown": finger_breakdown,
    }
