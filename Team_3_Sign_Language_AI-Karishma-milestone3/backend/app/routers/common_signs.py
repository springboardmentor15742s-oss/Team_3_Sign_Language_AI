import cv2
import numpy as np
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from app.models.user import User
from app.schemas.common_signs import CommonSignResponse, SupportedSignsResponse
from app.services.auth_dependency import get_current_user
from app.services.common_signs_service import SUPPORTED_SIGNS, recognize_common_sign

router = APIRouter(prefix="/api/common-signs", tags=["Common Signs"])


@router.get("/supported", response_model=SupportedSignsResponse)
def get_supported_signs():
    return SupportedSignsResponse(signs=SUPPORTED_SIGNS)


@router.post("/recognize", response_model=CommonSignResponse)
async def recognize(
    image: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """
    Runs an uploaded frame through the rule-based common-signs detector.
    Not logged as a PracticeAttempt — this is a standalone tester, separate
    from the scored alphabet curriculum and its accuracy/streak stats.
    """
    contents = await image.read()
    file_bytes = np.frombuffer(contents, dtype=np.uint8)
    decoded_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if decoded_image is None:
        raise HTTPException(status_code=400, detail="Could not decode uploaded image")

    result = recognize_common_sign(decoded_image)
    if result is None:
        return CommonSignResponse(detected_hand=False, sign=None, landmarks=None)

    return CommonSignResponse(
        detected_hand=True,
        sign=result["sign"],
        landmarks=result["landmarks"],
    )
