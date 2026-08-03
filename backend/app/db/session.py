import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
from app.core.config import settings

def create_db_engine():
    db_url = settings.DATABASE_URL
    if db_url.startswith("postgresql"):
        try:
            # Test PostgreSQL connection
            temp_engine = create_engine(
                db_url,
                pool_pre_ping=True,
                pool_size=5,
                max_overflow=10,
                connect_args={"connect_timeout": 3}
            )
            with temp_engine.connect() as conn:
                pass
            return temp_engine
        except (OperationalError, Exception) as e:
            print(f"[Database Warning] Could not connect to PostgreSQL on 5432 ({e}). Falling back to local SQLite database.")
            sqlite_url = "sqlite:///./signlang.db"
            fallback_engine = create_engine(
                sqlite_url,
                connect_args={"check_same_thread": False}
            )
            from app.models import Base
            Base.metadata.create_all(bind=fallback_engine)
            return fallback_engine
    else:
        engine = create_engine(db_url, connect_args={"check_same_thread": False})
        from app.models import Base
        Base.metadata.create_all(bind=engine)
        return engine

engine = create_db_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Auto-create tables for the active engine
from app.models import Base
Base.metadata.create_all(bind=engine)


def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
