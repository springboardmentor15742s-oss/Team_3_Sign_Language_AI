from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.auth import Token, UserRegisterRequest, UserLoginRequest, RefreshTokenRequest
from app.schemas.user import UserResponse
from app.services.auth_service import register_new_user, authenticate_user, generate_user_tokens, refresh_access_token
from app.api.deps import get_current_active_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """Register a new user (default role: learner)."""
    user = register_new_user(db, request)
    return user


@router.post("/login", response_model=Token)
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """Authenticate user with email and password to receive JWT access and refresh tokens."""
    user = authenticate_user(db, request)
    return generate_user_tokens(user)


@router.post("/refresh", response_model=Token)
def refresh_token(request: RefreshTokenRequest, db: Session = Depends(get_db)):
    """Obtain a new access token using a valid refresh token."""
    return refresh_access_token(db, request.refresh_token)


@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_active_user)):
    """Retrieve current authenticated user's profile details."""
    return current_user
