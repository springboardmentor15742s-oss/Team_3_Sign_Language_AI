from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class SupportedWordSignsResponse(BaseModel):
    words: list[str]
    # Honest model metadata surfaced to the frontend rather than implying
    # this is as reliable as the alphabet classifier — see
    # word_sign_service.get_model_info.
    model_test_accuracy: Optional[float] = None
    # word -> /media/... URL of a real reference photo (see
    # word_sign_service.get_reference_image_urls). A word missing from
    # this dict simply has no reference image yet.
    reference_images: dict[str, str] = {}


class WordSignResponse(BaseModel):
    # False when no pose/body reference was ever detected across the
    # sequence — distinct from a pose being tracked but the predicted
    # word not matching (word set, detected=True).
    detected: bool
    word: Optional[str] = None
    confidence: Optional[float] = None
    frame_count: int


class WordSignFeedbackResponse(BaseModel):
    # Null when status is no_attempt_detected — that outcome isn't
    # logged as a WordSignAttempt, same convention as
    # PracticeFeedbackResponse / MotionSignFeedbackResponse.
    attempt_id: Optional[str] = None
    status: str  # pass, fail, no_attempt_detected
    correct: Optional[bool] = None
    target_sign: str
    predicted_sign: Optional[str] = None
    confidence: Optional[float] = None
    feedback: str
    # Tiered feedback fields — same ai_feedback_service engine used by
    # practice.py / motion_signs.py (Milestone 3 integration).
    learner_level: Optional[str] = None
    error: Optional[str] = None
    improvement_tip: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
