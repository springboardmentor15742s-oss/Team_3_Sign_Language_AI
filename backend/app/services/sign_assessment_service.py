def assess_sign(gesture_result: dict | None, target_letter: str) -> dict:
    """
    Compares a gesture_recognition_service prediction against the letter
    the learner was asked to sign.

    gesture_result is None when no hand was detected in frame — that's a
    distinct "no attempt" state, not an incorrect answer, so it gets its
    own status rather than being scored as a fail.
    """
    if gesture_result is None:
        return {
            "status": "no_attempt_detected",
            "correct": None,
            "confidence": None,
            "target_letter": target_letter,
            "predicted_letter": None,
        }

    predicted_letter = gesture_result["letter"]
    confidence = gesture_result["confidence"]
    correct = predicted_letter == target_letter

    return {
        "status": "pass" if correct else "fail",
        "correct": correct,
        "confidence": confidence,
        "target_letter": target_letter,
        "predicted_letter": predicted_letter,
    }
