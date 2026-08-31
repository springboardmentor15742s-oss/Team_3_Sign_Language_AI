from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SupportedMotionSignsResponse(BaseModel):
    signs: list[str]


class MotionSignResponse(BaseModel):
    # False when hands weren't detected in enough frames of the sequence
    # to judge motion at all — distinct from hands being tracked but not
    # matching Wave or Clap (sign=None, detected=True).
    detected: bool
    sign: Optional[str] = None
    frame_count: int
    hands_detected_frames: Optional[int] = None


class MotionSignFeedbackResponse(BaseModel):
    # Null when status is no_attempt_detected — that outcome isn't logged
    # as a MotionSignAttempt, same convention as PracticeFeedbackResponse.
    attempt_id: Optional[str] = None
    status: str  # pass, fail, no_attempt_detected
    correct: Optional[bool] = None
    target_sign: str
    predicted_sign: Optional[str] = None
    feedback: str
    # Tiered feedback fields — see PracticeFeedbackResponse for why these
    # were added (Milestone 3 integration: wire the real tiered
    # ai_feedback_service engine into the submit flow instead of the
    # older plain pass/fail message).
    learner_level: Optional[str] = None
    error: Optional[str] = None
    improvement_tip: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
