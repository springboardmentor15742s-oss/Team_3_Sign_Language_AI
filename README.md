# AI-Powered Sign Language Learning & Assessment Platform

A web application designed to facilitate sign language education through AI-driven gesture recognition, interactive lessons, progress tracking, and role-based management.

---

## Technical Architecture

- **Frontend**: React 18, Vite, Tailwind CSS, Axios, React Router v6
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy 2.0 ORM, Alembic
- **Database**: PostgreSQL (with SQLite fallback for local test/dev)
- **Authentication**: JWT (Access + Refresh Token) with bcrypt password hashing
- **Deployment**: Docker & Docker Compose

---

## Milestone 1 Checklist

- [x] **Project initialization**: Clean frontend & backend repository architecture.
- [x] **System architecture**: Clear FastAPI backend and Vite React frontend layout.
- [x] **Database schema**: SQLAlchemy models for `User`, `Role`, and `LearnerProfile`.
- [x] **UI workflow**: Responsive wireframes for Landing, Register, Login, Dashboard, Profile, Progress, and Logout.
- [x] **Authentication**: Secure JWT tokens (Access + Refresh), password hashing (`bcrypt`), protected routes.
- [x] **Role-based access**: Full functionality for `Learner` and workspace placeholders for `Instructor`, `Accessibility Trainer`, and `Administrator`.
- [x] **Learner profile management**: View, edit, level selection, goals, progress stats, and profile picture upload.
- [x] **ASL dataset integration**: Automated detection of local ASL Alphabet Dataset (29 classes, train/test counts).
- [x] **Basic testing**: Automated test suite (`pytest`) validating auth, roles, profile, dataset service, and APIs.

---

## Quick Start Guide & Local Instructions

### Prerequisites
- Python 3.11+
- Node.js 18+
- PostgreSQL 14+ (optional for local SQLite testing) or Docker Desktop

### 1. Database Setup (Optional for PostgreSQL)
```sql
CREATE USER signlang_user WITH PASSWORD 'signlang_secure_pass';
CREATE DATABASE signlang_db OWNER signlang_user;
GRANT ALL PRIVILEGES ON DATABASE signlang_db TO signlang_user;
```

### 2. Backend Setup & Run
```bash
cd backend
python -m venv venv

# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# Unix / macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
Access interactive API Documentation at: `http://localhost:8000/docs`

### 3. Run Backend Automated Tests
```bash
cd backend
pytest tests/
```

### 4. Frontend Setup & Run
```bash
cd frontend
npm install
npm run dev
```
Access Web App at: `http://localhost:5173`

### 5. Dataset Summary Endpoint
`GET http://localhost:8000/api/v1/dataset/summary`

Returns JSON summary of detected ASL alphabet dataset without exposing raw images publicly.

### 6. Run with Docker Compose
```bash
docker compose up --build
```
