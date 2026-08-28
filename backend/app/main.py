from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.database import Base, engine
from app.routers import auth
from app.models import learner_profile  # adjust to your actual file/module name
from app.models import practice_attempt
from app.models import motion_sign_attempt
from app.models import learning_activity
from app.models import word_sign_attempt
from app.models import instructor_assignment

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sign Language Learning & Assessment Platform")

# Serves instructor-uploaded reference photos/videos (see
# media_upload_service) back to the frontend by relative path — e.g. a
# stored path "assignments/<uuid>.mp4" becomes GET /media/assignments/<uuid>.mp4.
UPLOAD_ROOT = Path(__file__).resolve().parent.parent / "data" / "uploads"
UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
app.mount("/media", StaticFiles(directory=str(UPLOAD_ROOT)), name="media")

app.add_middleware(
    CORSMiddleware,
    # CRA's default port (3000) isn't always free locally, so it falls back
    # to 3001/3002/etc. — match any localhost port rather than hardcoding
    # one, so a busy port doesn't silently break CORS again.
    allow_origin_regex=r"^http://localhost:\d+$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    # Content-Disposition isn't a CORS "simple" response header — without
    # exposing it explicitly, frontend JS can't read the PDF report's
    # server-generated filename from the response.
    expose_headers=["Content-Disposition"],
)

app.include_router(auth.router)
from app.routers import profile
app.include_router(profile.router)
from app.routers import practice
app.include_router(practice.router)
from app.routers import learner
app.include_router(learner.router)
from app.routers import instructor
app.include_router(instructor.router)
from app.routers import admin
app.include_router(admin.router)
from app.routers import reports
app.include_router(reports.router)
from app.routers import common_signs
app.include_router(common_signs.router)
from app.routers import motion_signs
app.include_router(motion_signs.router)
from app.routers import word_signs
app.include_router(word_signs.router)

@app.get("/")
def root():
    return {"message": "Sign Language Platform API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
