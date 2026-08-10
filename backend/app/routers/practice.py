import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.practice import PracticeFeedbackResponse
from app.services.auth_dependency import get_current_user
from app.services.feedback_service import generate_feedback, save_practice_attempt
from app.services.gesture_recognition_service import recognize_gesture
from app.services.sign_assessment_service import assess_sign

router = APIRouter(prefix="/api/practice", tags=["Practice"])

@router.post("/feedback", response_model=PracticeFeedbackResponse)
async def submit_practice_attempt(
    target_letter: str = Form(...),
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Runs an uploaded frame through gesture recognition + assessment, saves the attempt, and returns feedback."""
    contents = await image.read()
    file_bytes = np.frombuffer(contents, dtype=np.uint8)
    decoded_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if decoded_image is None:
        raise HTTPException(status_code=400, detail="Could not decode uploaded image")

    gesture_result = recognize_gesture(decoded_image)
    assessment = assess_sign(gesture_result, target_letter)
    feedback_text = generate_feedback(assessment)
    attempt = save_practice_attempt(db, current_user.id, assessment)

    return PracticeFeedbackResponse(
        attempt_id=attempt.id,
        status=assessment["status"],
        correct=assessment["correct"],
        confidence=assessment["confidence"],
        target_letter=assessment["target_letter"],
        predicted_letter=assessment["predicted_letter"],
        feedback=feedback_text,
        created_at=attempt.created_at,
    )
