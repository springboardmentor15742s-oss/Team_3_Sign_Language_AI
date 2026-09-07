"""
Shared pytest fixtures for the backend test suite.

DATABASE_URL is set BEFORE importing anything under app/ — app.database
reads it at import time (see app/database.py), so every test run gets
its own isolated SQLite file rather than touching the real dev database
(sign_language_platform.db) that a manually-run server would use. This
one line is what makes `pytest` from backend/ safe to run against a
machine that also has real dev/demo data sitting in the default db file.
"""

import os
import uuid
from pathlib import Path

TEST_DB_PATH = Path(__file__).resolve().parent / "test_sign_language_platform.db"
os.environ.setdefault("DATABASE_URL", f"sqlite:///{TEST_DB_PATH}")

# Deleted here — before app.database (and therefore its `engine`) is
# ever imported below — rather than in a fixture that runs afterward.
# Unlinking a SQLite file out from under an engine/connection that has
# already opened it produces exactly this kind of run: the file is gone
# from the directory but a pooled connection still holds the old inode
# open, so a later Base.metadata.create_all(bind=engine) call can end up
# writing to (or erroring against) that orphaned inode instead of a real
# file at this path — surfacing as a confusing "attempt to write a
# readonly database". Deleting first, before anything ever opens it,
# avoids the whole class of problem.
if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()

import pytest  # noqa: E402 — after the DATABASE_URL env var is set, on purpose
from fastapi.testclient import TestClient  # noqa: E402

from app.database import Base, engine, SessionLocal  # noqa: E402
from app.main import app  # noqa: E402
# Every model module must be imported somewhere before create_all runs,
# or Base.metadata simply won't know that table exists yet — app.main
# already imports the models it mounts routers for, but a couple
# (learner_profile) are only referenced indirectly, so re-imported here
# defensively rather than relying on import order elsewhere.
from app.models import (  # noqa: E402,F401
    certificate,
    instructor_assignment,
    instructor_learner,
    instructor_note,
    learner_profile,
    learning_activity,
    motion_sign_attempt,
    practice_attempt,
    word_sign_attempt,
)
from app.models.user import User  # noqa: E402
from app.services.auth_service import create_access_token, hash_password  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def _test_database():
    """The file itself was already deleted above, before import — this
    just makes sure every table exists (idempotent; app.main's own
    import-time create_all already does this too, but tests shouldn't
    rely on that happening to run first)."""
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture()
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture()
def db_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def make_user(db_session):
    """Factory fixture: make_user("Name", "email@test.com", "learner") -> User.
    Get-or-create by email, same convention scripts/test_*.py already
    used, so re-running a single test file twice in one session (or
    fixtures shared across tests in one module) never hits a UNIQUE
    constraint on email."""

    def _factory(name: str, email: str, role: str) -> User:
        user = db_session.query(User).filter(User.email == email).first()
        if user is None:
            user = User(
                id=str(uuid.uuid4()), name=name, email=email,
                hashed_password=hash_password("test-password"), role=role,
            )
            db_session.add(user)
            db_session.commit()
            db_session.refresh(user)
        return user

    return _factory


@pytest.fixture()
def auth_headers():
    """Factory fixture: auth_headers(user) -> {"Authorization": "Bearer ..."}"""

    def _factory(user: User) -> dict:
        return {"Authorization": f"Bearer {create_access_token({'sub': user.id})}"}

    return _factory
