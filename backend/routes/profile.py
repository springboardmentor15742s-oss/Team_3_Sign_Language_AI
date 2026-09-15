"""Learner profile management routes."""
from fastapi import APIRouter, Depends, HTTPException

from database import db
from deps import get_current_user
from schemas.models import ProfileIdentityRequest, ProfileOut, ProfileUpsertRequest

router = APIRouter(prefix="/api/profile", tags=["profile"])

# Keep the stored avatar small — this is a thumbnail, not a full photo
# library. The frontend already resizes to ~256px before upload; this is a
# server-side backstop against an oversized payload slipping through.
MAX_AVATAR_BASE64_CHARS = 400_000  # ~300KB


def _to_profile_out(row: dict) -> dict:
    goals = row["learning_goals"].split(",") if row.get("learning_goals") else []
    goals = [g for g in goals if g]
    return {
        "user_id": row["user_id"],
        "display_name": row.get("display_name") or None,
        "avatar_data": row.get("avatar_data") or None,
        "learning_level": row["learning_level"],
        "preferred_language": row["preferred_language"],
        "learning_goals": goals,
        "bio": row.get("bio") or "",
        "updated_at": row["updated_at"],
    }


@router.get("", response_model=ProfileOut)
def get_my_profile(current_user=Depends(get_current_user)):
    profile = db.get_learner_profile(current_user["id"])
    if not profile:
        raise HTTPException(status_code=404, detail="No profile set up yet.")
    return _to_profile_out(profile)


@router.put("", response_model=ProfileOut)
def upsert_my_profile(payload: ProfileUpsertRequest, current_user=Depends(get_current_user)):
    db.upsert_learner_profile(
        user_id=current_user["id"],
        learning_level=payload.learning_level,
        preferred_language=payload.preferred_language,
        learning_goals=payload.learning_goals,
        bio=payload.bio,
    )
    profile = db.get_learner_profile(current_user["id"])
    return _to_profile_out(profile)


@router.put("/identity", response_model=ProfileOut)
def update_identity(payload: ProfileIdentityRequest, current_user=Depends(get_current_user)):
    """Updates the profile photo + display name shown in the Navbar and
    the top of the Profile page — separate from learning preferences so
    the two forms can save independently."""
    if payload.avatar_data and len(payload.avatar_data) > MAX_AVATAR_BASE64_CHARS:
        raise HTTPException(status_code=400, detail="Image is too large — please use a smaller photo.")
    row = db.update_profile_identity(current_user["id"], payload.display_name, payload.avatar_data)
    return _to_profile_out(row)
