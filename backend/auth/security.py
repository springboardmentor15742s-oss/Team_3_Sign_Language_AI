"""Password hashing + JWT issuing/verification for the FastAPI backend."""
import hashlib
import os
import re
from datetime import datetime, timedelta, timezone

import jwt

from config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES, ROLES
from database import db

EMAIL_REGEX = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _hash_password(password: str, salt: str) -> str:
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


def _generate_salt() -> str:
    return os.urandom(16).hex()


def validate_registration(username, email, password, role):
    if not username or len(username) < 3:
        return False, "Username must be at least 3 characters long."
    if not email or not EMAIL_REGEX.match(email):
        return False, "Please enter a valid email address."
    if not password or len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if role not in ROLES:
        return False, "Invalid role selected."
    if db.username_or_email_exists(username, email):
        return False, "Username or email already registered."
    return True, ""


def register_user(username, email, password, role):
    salt = _generate_salt()
    password_hash = _hash_password(password, salt)
    user_id = db.create_user(username, email, password_hash, salt, role)
    return user_id


def authenticate_user(username, password):
    user = db.get_user_by_username(username)
    if not user or not user.get("is_active", 1):
        return None
    if _hash_password(password, user["salt"]) == user["password_hash"]:
        return user
    return None


def create_access_token(user: dict) -> str:
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "role": user["role"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.PyJWTError:
        return None
