from fastapi import APIRouter, Depends, UploadFile, File, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.learner_profile import (
    LearnerProfileResponse,
    LearnerProfileUpdateRequest,
    LearnerProgressUpdateRequest,
)
from app.services import learner_profile_service
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/learner-profiles", tags=["Learner Profiles"])


@router.get("/me", response_model=LearnerProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Fetch current user's learner profile."""
    return learner_profile_service.get_profile_by_user_id(db, current_user.id)


@router.put("/me", response_model=LearnerProfileResponse)
def update_my_profile(
    request: LearnerProfileUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's profile details."""
    return learner_profile_service.update_profile(db, current_user.id, request)


@router.patch("/me/progress", response_model=LearnerProfileResponse)
def update_my_progress(
    request: LearnerProgressUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Update current user's learning progress metrics."""
    return learner_profile_service.update_progress(db, current_user.id, request)


@router.post("/me/picture", response_model=LearnerProfileResponse)
def upload_my_profile_picture(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Upload a profile picture for current user."""
    return learner_profile_service.save_profile_picture(db, current_user.id, file)
