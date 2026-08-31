import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.learner_profile import LearnerProfile
from app.schemas.learner_profile import LearnerProfileUpdate, LearnerProfileResponse
from app.services.auth_dependency import get_current_user

router = APIRouter(prefix="/api/profile", tags=["Learner Profile"])

@router.get("/me", response_model=LearnerProfileResponse)
def get_my_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get the logged-in learner's profile. Creates one automatically if it doesn't exist yet."""
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        profile = LearnerProfile(id=str(uuid.uuid4()), user_id=current_user.id)
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


@router.put("/me", response_model=LearnerProfileResponse)
def update_my_profile(
    updates: LearnerProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update the logged-in learner's profile fields."""
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == current_user.id).first()
    if not profile:
        profile = LearnerProfile(id=str(uuid.uuid4()), user_id=current_user.id)
        db.add(profile)

    if updates.learning_level is not None:
        profile.learning_level = updates.learning_level
    if updates.preferred_language is not None:
        profile.preferred_language = updates.preferred_language
    if updates.learning_goals is not None:
        profile.learning_goals = updates.learning_goals

    db.commit()
    db.refresh(profile)
    return profile