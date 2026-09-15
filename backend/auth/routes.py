"""Authentication routes: register, login, current-user info."""
from fastapi import APIRouter, Depends, HTTPException, status

from auth.security import (
    authenticate_user,
    create_access_token,
    register_user,
    validate_registration,
)
from auth.security import _generate_salt, _hash_password
from database import db
from deps import get_current_user
from schemas.models import ChangePasswordRequest, LoginRequest, RegisterRequest, TokenResponse, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest):
    is_valid, error_msg = validate_registration(
        payload.username, payload.email, payload.password, payload.role
    )
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    user_id = register_user(payload.username, payload.email, payload.password, payload.role)
    user = db.get_user_by_id(user_id)
    return user


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest):
    user = authenticate_user(payload.username, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username/password, or account inactive.")
    token = create_access_token(user)
    return {"access_token": token, "token_type": "bearer", "user": user}


@router.get("/me", response_model=UserOut)
def me(current_user=Depends(get_current_user)):
    return current_user


@router.post("/change-password")
def change_password(payload: ChangePasswordRequest, current_user=Depends(get_current_user)):
    """Account Settings — verifies the current password before allowing a
    new one, same salted-hash scheme used at registration."""
    user = db.get_user_by_id(current_user["id"])
    if _hash_password(payload.current_password, user["salt"]) != user["password_hash"]:
        raise HTTPException(status_code=400, detail="Current password is incorrect.")
    if len(payload.new_password) < 6:
        raise HTTPException(status_code=400, detail="New password must be at least 6 characters long.")

    new_salt = _generate_salt()
    new_hash = _hash_password(payload.new_password, new_salt)
    db.update_password(current_user["id"], new_hash, new_salt)
    return {"message": "Password updated successfully."}
