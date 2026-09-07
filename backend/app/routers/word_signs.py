import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.word_signs import (
    SupportedWordSignsResponse,
    WordSignFeedbackResponse,
    WordSignResponse,
)
from app.services.adaptive_learning_service import get_adaptive_learning_plan
from app.services.ai_feedback_service import generate_activity_feedback
from app.services.auth_dependency import get_current_user
from app.services.certificate_service import sync_auto_certificates
from app.services.word_sign_service import (
    assess_word_sign,
    get_model_info,
    get_reference_image_urls,
    get_supported_word_signs,
    recognize_word_sign,
    save_word_sign_attempt,
)

router = APIRouter(prefix="/api/word-signs", tags=["Word Signs"])

# A capture much shorter than this can't contain a full word sign;
# much longer wastes upload bandwidth for no benefit — same bounds
# reasoning as routers/motion_signs.py.
MIN_FRAMES = 8
MAX_FRAMES = 90


def _decode_frames(images: list[UploadFile]) -> list:
    if not (MIN_FRAMES <= len(images) <= MAX_FRAMES):
        raise HTTPException(
            status_code=400,
            detail=f"Expected between {MIN_FRAMES} and {MAX_FRAMES} frames, got {len(images)}",
        )

    frames = []
    for image in images:
        file_bytes = np.frombuffer(image.file.read(), dtype=np.uint8)
        decoded = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if decoded is None:
            raise HTTPException(status_code=400, detail="Could not decode one or more uploaded frames")
        frames.append(decoded)
    return frames


@router.get("/supported", response_model=SupportedWordSignsResponse)
def get_supported():
    info = get_model_info()
    return SupportedWordSignsResponse(
        words=get_supported_word_signs(),
        model_test_accuracy=info["test_accuracy"],
        reference_images=get_reference_image_urls(),
    )


@router.post("/recognize", response_model=WordSignResponse)
async def recognize(
    images: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Runs an uploaded frame sequence through the trained word-sign
    classifier. Not logged as a WordSignAttempt — a standalone tester,
    same role /api/motion-signs/recognize plays for gestures.
    """
    frames = _decode_frames(images)
    result = recognize_word_sign(frames)
    if result is None:
        return WordSignResponse(detected=False, word=None, confidence=None, frame_count=len(frames))

    return WordSignResponse(
        detected=True,
        word=result["word"],
        confidence=result["confidence"],
        frame_count=result["frame_count"],
    )


@router.post("/feedback", response_model=WordSignFeedbackResponse)
async def submit_word_sign_attempt(
    target_word: str = Form(...),
    images: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Runs an uploaded frame sequence through the trained classifier,
    saves the attempt, and returns feedback through the same
    skill-tiered ai_feedback_service engine practice.py / motion_signs.py
    use (Milestone 3 integration: one feedback chain for every topic
    type on this platform).
    """
    if target_word not in get_supported_word_signs():
        raise HTTPException(status_code=400, detail=f"Unsupported target_word: {target_word}")

    frames = _decode_frames(images)
    recognition = recognize_word_sign(frames)
    assessment = assess_word_sign(recognition, target_word)

    learner_level = get_adaptive_learning_plan(db, current_user.id)["learning_level"]
    activity_feedback = generate_activity_feedback(assessment, learner_level, topic_type="word_sign")

    attempt_id = None
    created_at = None
    if assessment["status"] != "no_attempt_detected":
        attempt = save_word_sign_attempt(db, current_user.id, assessment)
        attempt_id = attempt.id
        created_at = attempt.created_at
        sync_auto_certificates(db, current_user.id, "conversational-fluency")

    return WordSignFeedbackResponse(
        attempt_id=attempt_id,
        status=assessment["status"],
        correct=assessment["correct"],
        target_sign=assessment["target_sign"],
        predicted_sign=assessment["predicted_sign"],
        confidence=assessment["confidence"],
        feedback=activity_feedback["message"],
        learner_level=activity_feedback["learner_level"],
        error=activity_feedback["error"],
        improvement_tip=activity_feedback["improvement_tip"],
        created_at=created_at,
    )
