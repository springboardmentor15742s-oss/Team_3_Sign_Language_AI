from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.routers import auth
from app.models import learner_profile  # adjust to your actual file/module name
from app.models import practice_attempt

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sign Language Learning & Assessment Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
from app.routers import profile
app.include_router(profile.router)
from app.routers import practice
app.include_router(practice.router)
from app.routers import learner
app.include_router(learner.router)

@app.get("/")
def root():
    return {"message": "Sign Language Platform API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}