from typing import List, Callable
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.user import User
from app.core.security import decode_jwt_token
from app.core.exceptions import CredentialsException, PermissionDeniedException

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme)
) -> User:
    payload = decode_jwt_token(token)
    if not payload or payload.get("type") != "access":
        raise CredentialsException(detail="Could not validate access token")

    user_id: str = payload.get("sub")
    if user_id is None:
        raise CredentialsException(detail="Invalid token subject")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if user is None:
        raise CredentialsException(detail="User not found")
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise CredentialsException(detail="Inactive user account")
    return current_user


def require_roles(allowed_roles: List[str]) -> Callable:
    """Dependency factory to enforce Role-Based Access Control (RBAC)."""
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise PermissionDeniedException(
                detail=f"Role '{current_user.role.name}' is not authorized to access this resource."
            )
        return current_user

    return role_checker
