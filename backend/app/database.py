import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Overridable via DATABASE_URL so the test suite (tests/conftest.py) can
# point this at its own isolated SQLite file instead of the real dev
# database — must be set before this module is first imported, since
# everything below is bound at import time. Unset (the normal app run),
# this is unchanged from before.
SQLALCHEMY_DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./sign_language_platform.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()