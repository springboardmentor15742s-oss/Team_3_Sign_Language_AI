"""
Sign Language Learning & Assessment Platform — Milestone 1 Backend (FastAPI)

Run with:
    uvicorn main:app --reload --port 8000
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import APP_TITLE, FRONTEND_ORIGINS
from database.db import init_db

from auth.routes import router as auth_router
from routes.profile import router as profile_router
from routes.dashboard import router as dashboard_router
from routes.datasets import router as datasets_router
from routes.admin import router as admin_router
from routes.gesture import router as gesture_router
from routes.intelligence import router as intelligence_router
from routes.certification import router as certification_router
from routes.reports import router as reports_router
from routes.courses import router as courses_router
from routes.notifications import router as notifications_router
from routes.quiz import router as quiz_router
from courses.seed_data import seed_courses_if_empty
from quiz.seed_data import seed_quiz_questions_if_empty

app = FastAPI(title=APP_TITLE, version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONTEND_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    seed_courses_if_empty()
    seed_quiz_questions_if_empty()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": APP_TITLE}


app.include_router(auth_router)
app.include_router(profile_router)
app.include_router(dashboard_router)
app.include_router(datasets_router)
app.include_router(admin_router)
app.include_router(gesture_router)
app.include_router(intelligence_router)
app.include_router(certification_router)
app.include_router(reports_router)
app.include_router(courses_router)
app.include_router(notifications_router)
app.include_router(quiz_router)
