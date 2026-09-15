"""Admin routes: user management, dataset log oversight (Administrator only)."""
from fastapi import APIRouter, Depends, HTTPException

from certification.rules import LEVELS
from config import ROLES
from database import db
from deps import require_roles
from schemas.models import ActiveUpdateRequest, LevelUpdateRequest, RoleUpdateRequest

router = APIRouter(prefix="/api/admin", tags=["admin"])


@router.get("/users")
def list_users(current_user=Depends(require_roles("Administrator"))):
    return db.list_all_users()


@router.put("/users/{user_id}/role")
def update_role(user_id: int, payload: RoleUpdateRequest, current_user=Depends(require_roles("Administrator"))):
    if payload.role not in ROLES:
        raise HTTPException(status_code=400, detail="Invalid role.")
    if not db.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found.")
    db.update_user_role(user_id, payload.role)
    return db.get_user_by_id(user_id)


@router.put("/users/{user_id}/active")
def update_active(user_id: int, payload: ActiveUpdateRequest, current_user=Depends(require_roles("Administrator"))):
    if not db.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found.")
    db.set_user_active(user_id, payload.is_active)
    return db.get_user_by_id(user_id)


@router.put("/users/{user_id}/level")
def update_learner_level(user_id: int, payload: LevelUpdateRequest, current_user=Depends(require_roles("Administrator"))):
    """Admin override of a learner's level — e.g. to manually place an
    experienced learner at Intermediate instead of making them re-earn it
    through practice attempts."""
    if payload.level not in LEVELS:
        raise HTTPException(status_code=400, detail=f"Invalid level. Choose one of: {', '.join(LEVELS)}")
    if not db.get_user_by_id(user_id):
        raise HTTPException(status_code=404, detail="User not found.")
    db.set_learner_level(user_id, payload.level)
    users = db.list_all_users()
    return next(u for u in users if u["id"] == user_id)
