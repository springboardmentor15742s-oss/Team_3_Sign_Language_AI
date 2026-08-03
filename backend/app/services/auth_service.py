from typing import Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.role import Role, RoleName
from app.models.learner_profile import LearnerProfile
from app.schemas.auth import UserRegisterRequest, UserLoginRequest
from app.core.security import get_password_hash, verify_password, create_access_token, create_refresh_token, decode_jwt_token
from app.core.exceptions import ConflictException, CredentialsException, NotFoundException


def get_role_by_name(db: Session, role_name: str) -> Role:
    role = db.query(Role).filter(Role.name == role_name.lower()).first()
    if not role:
        # Fallback or auto-create default roles if empty
        role = Role(name=role_name.lower(), description=f"{role_name.capitalize()} role")
        db.add(role)
        db.commit()
        db.refresh(role)
    return role


def seed_default_roles(db: Session):
    """Seed initial roles if database is empty."""
    default_roles = [
        (RoleName.LEARNER.value, "Default student/learner account"),
        (RoleName.INSTRUCTOR.value, "Content manager and assessment instructor"),
        (RoleName.ACCESSIBILITY_TRAINER.value, "Accessibility workflows & trainer"),
        (RoleName.ADMINISTRATOR.value, "Full system administration"),
    ]
    for name, desc in default_roles:
        existing = db.query(Role).filter(Role.name == name).first()
        if not existing:
            db.add(Role(name=name, description=desc))
    db.commit()


def register_new_user(db: Session, request: UserRegisterRequest) -> User:
    # Ensure default roles exist
    seed_default_roles(db)

    # Check for existing email or username
    if db.query(User).filter(User.email == request.email).first():
        raise ConflictException(detail="An account with this email already exists")

    if db.query(User).filter(User.username == request.username).first():
        raise ConflictException(detail="Username is already taken")

    # Get requested or default role
    role = get_role_by_name(db, request.role_name or RoleName.LEARNER.value)

    # Create User
    new_user = User(
        email=request.email,
        username=request.username,
        hashed_password=get_password_hash(request.password),
        role_id=role.id,
        is_active=True,
        is_verified=False
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Create associated LearnerProfile
    profile = LearnerProfile(
        user_id=new_user.id,
        full_name=request.full_name or request.username,
        learning_level="beginner",
        preferred_language="ASL"
    )
    db.add(profile)
    db.commit()
    db.refresh(new_user)

    return new_user


def authenticate_user(db: Session, request: UserLoginRequest) -> User:
    user = db.query(User).filter(User.email == request.email).first()
    if not user:
        raise CredentialsException(detail="Invalid email or password")

    if not verify_password(request.password, user.hashed_password):
        raise CredentialsException(detail="Invalid email or password")

    if not user.is_active:
        raise CredentialsException(detail="Account is inactive")

    return user


def generate_user_tokens(user: User) -> dict:
    access_token = create_access_token(subject=user.id, role=user.role.name)
    refresh_token = create_refresh_token(subject=user.id)
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


def refresh_access_token(db: Session, refresh_token: str) -> dict:
    payload = decode_jwt_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise CredentialsException(detail="Invalid or expired refresh token")

    user_id = payload.get("sub")
    if not user_id:
        raise CredentialsException(detail="Invalid token payload")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user or not user.is_active:
        raise CredentialsException(detail="User not found or inactive")

    return generate_user_tokens(user)
