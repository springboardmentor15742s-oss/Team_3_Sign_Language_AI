from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HandLandmarkPoint(BaseModel):
    x: float
    y: float
    z: float


class SupportedLettersResponse(BaseModel):
    letters: list[str]


class PracticeRecognizeResponse(BaseModel):
    # False when no hand was found in frame at all — distinct from a hand
    # being present but not matching any letter confidently (which the
    # model doesn't represent separately; it always returns its best
    # guess plus a confidence score once a hand is found). Mirrors
    # MotionSignResponse / WordSignResponse / CommonSignResponse's own
    # detected/not-detected split.
    detected: bool
    predicted_letter: Optional[str] = None
    confidence: Optional[float] = None
    landmarks: Optional[list[HandLandmarkPoint]] = None


class PracticeFeedbackResponse(BaseModel):
    # Null when status is no_attempt_detected — that outcome is not logged
    # as a PracticeAttempt, so there's no row to reference.
    attempt_id: Optional[str] = None
    status: str  # pass, fail, no_attempt_detected
    correct: Optional[bool] = None
    confidence: Optional[float] = None
    target_letter: str
    predicted_letter: Optional[str] = None
    feedback: str
    # Tiered feedback fields (ai_feedback_service.generate_activity_feedback)
    # — added for the Milestone 3 integration task so the immediate
    # per-attempt response reflects the same skill-tiered engine the
    # dashboard's aggregate feedback already used, instead of the older
    # plain pass/fail one-liner. learner_level is the learner's tier
    # (beginner/intermediate/advanced) at the moment of this attempt;
    # error/improvement_tip are null on a pass, populated on fail or
    # no_attempt_detected.
    learner_level: Optional[str] = None
    error: Optional[str] = None
    improvement_tip: Optional[str] = None
    created_at: Optional[datetime] = None
    # Raw MediaPipe hand landmarks (normalized image-space x/y/z) for the
    # captured frame, for the result overlay — null whenever no hand was
    # detected, same as predicted_letter.
    landmarks: Optional[list[HandLandmarkPoint]] = None

    class Config:
        from_attributes = True
