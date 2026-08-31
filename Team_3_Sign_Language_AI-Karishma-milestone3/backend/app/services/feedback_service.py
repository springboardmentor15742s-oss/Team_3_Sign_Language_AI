import uuid

from sqlalchemy.orm import Session

from app.models.practice_attempt import PracticeAttempt

FEEDBACK_MESSAGES = {
    "pass": "Nice work! Your '{target_letter}' sign was correct — keep it up.",
    "fail": "Not quite — that didn't match '{target_letter}'. Check your hand shape and try again.",
    "no_attempt_detected": "We couldn't detect your hand. Make sure it's clearly visible in frame and try again.",
}


def generate_feedback(assessment_result: dict) -> str:
    """
    Turns a sign_assessment_service result into learner-facing feedback
    text. We don't have per-finger diagnostic detail, so the fail
    message stays a generic-but-honest hint rather than fabricating
    specific corrections we can't actually detect.
    """
    status = assessment_result["status"]
    if status not in FEEDBACK_MESSAGES:
        raise ValueError(f"Unknown assessment status: {status}")

    return FEEDBACK_MESSAGES[status].format(target_letter=assessment_result["target_letter"])


def save_practice_attempt(db: Session, learner_id: str, assessment_result: dict) -> PracticeAttempt:
    """
    Persists a sign_assessment_service result (pass, fail, or
    no_attempt_detected) as a PracticeAttempt row.
    """
    attempt = PracticeAttempt(
        id=str(uuid.uuid4()),
        learner_id=learner_id,
        target_letter=assessment_result["target_letter"],
        predicted_letter=assessment_result["predicted_letter"],
        status=assessment_result["status"],
        correct=assessment_result["correct"],
        confidence=assessment_result["confidence"],
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt
