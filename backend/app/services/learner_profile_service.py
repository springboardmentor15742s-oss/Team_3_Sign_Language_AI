import os
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import UploadFile
from app.models.learner_profile import LearnerProfile
from app.schemas.learner_profile import LearnerProfileUpdateRequest, LearnerProgressUpdateRequest
from app.core.config import settings
from app.core.exceptions import NotFoundException, HTTPException


def get_profile_by_user_id(db: Session, user_id: int) -> LearnerProfile:
    profile = db.query(LearnerProfile).filter(LearnerProfile.user_id == user_id).first()
    if not profile:
        # Create fallback profile if missing
        profile = LearnerProfile(user_id=user_id, learning_level="beginner", preferred_language="ASL")
        db.add(profile)
        db.commit()
        db.refresh(profile)
    return profile


def update_profile(db: Session, user_id: int, request: LearnerProfileUpdateRequest) -> LearnerProfile:
    profile = get_profile_by_user_id(db, user_id)

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(profile, field, value)

    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


def update_progress(db: Session, user_id: int, request: LearnerProgressUpdateRequest) -> LearnerProfile:
    profile = get_profile_by_user_id(db, user_id)

    if request.total_points is not None:
        profile.total_points = request.total_points
    if request.current_streak is not None:
        profile.current_streak = request.current_streak
    if request.completed_lessons_count is not None:
        profile.completed_lessons_count = request.completed_lessons_count

    profile.last_active_at = datetime.utcnow()
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile


def save_profile_picture(db: Session, user_id: int, file: UploadFile) -> LearnerProfile:
    profile = get_profile_by_user_id(db, user_id)

    # Validate image extension
    allowed_extensions = {".jpg", ".jpeg", ".png", ".webp"}
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type '{file_ext}'. Allowed types: {', '.join(allowed_extensions)}"
        )

    # Generate unique filename
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    filename = f"user_{user_id}_{uuid.uuid4().hex[:8]}{file_ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    # Save to disk
    contents = file.file.read()
    if len(contents) > settings.MAX_UPLOAD_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File size exceeds maximum limit of {settings.MAX_UPLOAD_SIZE_BYTES / (1024*1024):.1f} MB"
        )

    with open(file_path, "wb") as f:
        f.write(contents)

    relative_url = f"/uploads/{filename}"
    profile.profile_picture_url = relative_url
    profile.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(profile)
    return profile
