"""Central configuration for the FastAPI backend (Milestone 1)."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Allows Docker/production deployments to point the SQLite file at a
# mounted volume (see backend/Dockerfile) without touching this file.
DB_PATH = os.environ.get("DB_PATH", os.path.join(BASE_DIR, "platform.db"))
SAMPLE_DATA_DIR = os.path.join(BASE_DIR, "datasets", "sample_data")
DATASETS_DIR = os.path.join(BASE_DIR, "datasets", "raw")
PROCESSED_DIR = os.path.join(BASE_DIR, "datasets", "processed")

ROLES = ["Learner", "Instructor", "Accessibility Trainer", "Administrator"]

LEARNING_LEVELS = ["Beginner", "Intermediate", "Advanced", "Professional"]

# --- Course & Content Service ---------------------------------------------
# Matches the "Course Categories" list in the project spec.
COURSE_CATEGORIES = [
    "Beginner Sign Language",
    "Intermediate Sign Language",
    "Advanced Sign Language",
    "Everyday Communication",
    "Educational Vocabulary",
    "Professional Communication",
]
COURSE_LEVELS = LEARNING_LEVELS
# Roles allowed to create/manage courses & lessons (Course & Content Service).
COURSE_MANAGER_ROLES = ["Instructor", "Accessibility Trainer", "Administrator"]
PREFERRED_LANGUAGES = [
    "ASL (American Sign Language)",
    "BSL (British Sign Language)",
    "ISL (Indian Sign Language)",
    "Other",
]
LEARNING_GOAL_OPTIONS = [
    "Everyday Communication",
    "Educational Vocabulary",
    "Professional Communication",
    "Certification Preparation",
]

RECOMMENDED_DATASETS = {
    "ASL Alphabet Dataset": {
        "purpose": ["Sign language alphabet recognition", "Gesture classification"],
        "kaggle_slug": "grassknoted/asl-alphabet",
    },
    "Sign Language MNIST Dataset": {
        "purpose": ["Static sign recognition", "Gesture classification training"],
        "kaggle_slug": "datamunge/sign-language-mnist",
    },
    "WLASL Dataset": {
        "purpose": ["Dynamic sign recognition", "Continuous sign language learning"],
        "kaggle_slug": "risangbaskoro/wlasl-processed",
    },
    "RWTH-PHOENIX Dataset": {
        "purpose": ["Sign language translation", "Sequence recognition"],
        "kaggle_slug": None,
        "info_url": "https://www-i6.informatik.rwth-aachen.de/~koller/RWTH-PHOENIX/",
    },
}

# --- Auth / JWT ----------------------------------------------------------
JWT_SECRET = os.environ.get("JWT_SECRET", "milestone1-dev-secret-change-me")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24  # 24 hours

# --- CORS ------------------------------------------------------------------
FRONTEND_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

APP_TITLE = "Sign Language Learning & Assessment Platform — API"
