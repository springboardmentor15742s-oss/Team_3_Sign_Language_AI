import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.motion_signs import (
    MotionSignFeedbackResponse,
    MotionSignResponse,
    SupportedMotionSignsResponse,
)
from app.services.auth_dependency import get_current_user
from app.services.motion_sign_service import (
    SUPPORTED_MOTION_SIGNS,
    assess_motion_sign,
    recognize_motion_sign,
    save_motion_sign_attempt,
)

router = APIRouter(prefix="/api/motion-signs", tags=["Motion Signs"])

# A capture much shorter than this can't contain a full wave/clap motion;
# much longer wastes upload bandwidth for no benefit. Not a hard
# validation limit — just a sanity bound so a malformed request fails
# clearly instead of the detector silently returning a low-confidence None.
MIN_FRAMES = 5
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


@router.get("/supported", response_model=SupportedMotionSignsResponse)
def get_supported_motion_signs():
    return SupportedMotionSignsResponse(signs=SUPPORTED_MOTION_SIGNS)


@router.post("/recognize", response_model=MotionSignResponse)
async def recognize(
    images: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Runs an uploaded frame sequence through the rule-based motion
    detector. Not logged as a MotionSignAttempt — a standalone tester,
    same role /api/common-signs/recognize plays for static signs.
    """
    frames = _decode_frames(images)
    result = recognize_motion_sign(frames)
    if result is None:
        return MotionSignResponse(detected=False, sign=None, frame_count=len(frames), hands_detected_frames=0)

    return MotionSignResponse(
        detected=True,
        sign=result["sign"],
        frame_count=result["frame_count"],
        hands_detected_frames=result["hands_detected_frames"],
    )


@router.post("/feedback", response_model=MotionSignFeedbackResponse)
async def submit_motion_sign_attempt(
    target_sign: str = Form(...),
    images: list[UploadFile] = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Runs an uploaded frame sequence through motion recognition, saves the attempt, and returns feedback."""
    if target_sign not in SUPPORTED_MOTION_SIGNS:
        raise HTTPException(status_code=400, detail=f"Unsupported target_sign: {target_sign}")

    frames = _decode_frames(images)
    motion_result = recognize_motion_sign(frames)
    assessment = assess_motion_sign(motion_result, target_sign)

    feedback_messages = {
        "pass": f"Nice work! Your '{target_sign}' matched.",
        "fail": f"Not quite — that didn't match '{target_sign}'. Try a bigger, clearer motion and try again.",
        "no_attempt_detected": "We couldn't track your hand(s) through enough of the clip. Make sure they're clearly visible and try again.",
    }

    attempt_id = None
    created_at = None
    if assessment["status"] != "no_attempt_detected":
        attempt = save_motion_sign_attempt(db, current_user.id, assessment)
        attempt_id = attempt.id
        created_at = attempt.created_at

    return MotionSignFeedbackResponse(
        attempt_id=attempt_id,
        status=assessment["status"],
        correct=assessment["correct"],
        target_sign=assessment["target_sign"],
        predicted_sign=assessment["predicted_sign"],
        feedback=feedback_messages[assessment["status"]],
        created_at=created_at,
    )
