# Sign Language Learning & Assessment Platform
## Milestones 1, 2, 3 & 4 — Full Merged Build (Week 1–8)

This is the **React + FastAPI** build of the Infosys Springboard "AI-powered
Sign Language Learning & Assessment Platform" project, covering the entire
8-week roadmap:

- **Milestone 1** (Week 1 & 2) — Project Initialization, Design Process & Core Setup
- **Milestone 2** (Week 3 & 4) — Gesture Recognition Engine, Hand Tracking & Accuracy Assessment
- **Milestone 3** (Week 5 & 6) — AI Feedback & Learning Intelligence Engine
- **Milestone 4** (Week 7 & 8) — Certification, Testing & Deployment

All four milestones live in the **same codebase** — each was built directly
on top of the previous one, not as a separate app, so everything (auth,
profiles, datasets, gesture practice, learning intelligence, certification,
and reporting) works together in one run. See `docs/milestone2_gesture_engine.md`,
`docs/milestone3_learning_intelligence.md`, and
`docs/milestone4_certification_reporting.md` for the full design writeups.

---

## 1. Project Structure

```
sign-language-milestone3/
├── backend/                       # FastAPI application
│   ├── main.py                    # App entry point, CORS, router registration
│   ├── config.py                  # App-wide configuration & constants
│   ├── deps.py                    # JWT auth + RBAC FastAPI dependencies
│   ├── requirements.txt
│   ├── requirements-dev.txt       # (M4) pytest + httpx for the test suite
│   ├── Dockerfile                 # (M4) backend container image
│   ├── .dockerignore
│   ├── .env.example
│   │
│   ├── database/
│   │   ├── db.py                  # SQLite connection + CRUD helpers
│   │   └── schema.sql             # users, learner_profiles, gesture_attempts,
│   │                               # assessment_reports, certificates, dataset_log
│   │
│   ├── auth/
│   │   ├── security.py            # Password hashing, JWT issue/verify
│   │   └── routes.py              # POST /register, /login, GET /me
│   │
│   ├── schemas/
│   │   └── models.py              # Pydantic request/response models
│   │
│   ├── routes/
│   │   ├── profile.py             # GET/PUT /api/profile
│   │   ├── dashboard.py           # GET /api/dashboard, POST /log-activity
│   │   ├── datasets.py            # dataset explore/preview/preprocess endpoints
│   │   ├── admin.py               # Administrator-only user management
│   │   ├── gesture.py             # (M2) detect / assess / history / stats endpoints
│   │   ├── intelligence.py        # (M3) analytics / feedback / recommendations / report
│   │   ├── certification.py       # (M4) eligibility / issue / verify / my / all
│   │   └── reports.py             # (M4) learning / accuracy / progress / certification / class-overview
│   │
│   ├── gesture/                   # Milestone 2 — Gesture Recognition & Assessment
│   │   ├── landmarks.py           # MediaPipe Hands wrapper (21-point hand tracking)
│   │   ├── classifier.py          # Finger-state geometric gesture classifier
│   │   ├── reference_signs.py     # Reference gesture library (patterns + descriptions)
│   │   └── accuracy.py            # Sign Accuracy Assessment Engine + feedback generation
│   │
│   ├── intelligence/              # Milestone 3 — AI Feedback & Learning Intelligence
│   │   ├── analytics.py           # Learning Analytics (pandas + sklearn): accuracy, skill levels, trend
│   │   ├── feedback.py            # AI Feedback & Correction Engine: strengths/weaknesses, common mistakes
│   │   ├── recommendations.py     # Recommendation Engine: practice counts + scikit-learn trend/forecast
│   │   ├── learning_plan.py       # Personalized Learning Plan: today's ordered practice plan
│   │   └── report.py              # Assessment Report Generator: JSON + downloadable text report
│   │
│   ├── certification/             # Milestone 4 — Certification Workflows
│   │   └── rules.py               # 4-level eligibility rules, code generation, certificate text
│   │
│   ├── reporting/                 # Milestone 4 — Reporting Modules
│   │   └── reports.py             # CSV builders: accuracy / progress / certification / class-overview
│   │
│   ├── tests/                     # Milestone 4 — automated test suite (pytest)
│   │   ├── conftest.py            # isolated temp-SQLite-DB fixture per test
│   │   └── test_milestone4.py     # certification + reporting endpoint tests
│   │
│   └── datasets/
│       ├── dataset_downloader.py  # Downloads ASL/MNIST/WLASL/PHOENIX (run locally)
│       ├── dataset_explorer.py    # Folder structure / label distribution / format report
│       ├── preprocessing.py       # Resize/normalize pipeline
│       ├── generate_sample_data.py# Builds the bundled synthetic demo dataset
│       └── sample_data/           # Synthetic offline demo dataset (5 classes)
│
├── frontend/                      # React (Vite) single-page app
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   ├── Dockerfile                 # (M4) multi-stage build -> nginx
│   ├── nginx.conf                 # (M4) SPA fallback routing
│   ├── .dockerignore
│   ├── .env.example
│   └── src/
│       ├── main.jsx               # React entry point
│       ├── App.jsx                # Router setup
│       ├── api.js                 # fetch()-based API client
│       ├── styles.css             # Global styling (no UI framework dependency)
│       ├── context/
│       │   └── AuthContext.jsx    # JWT session state (login/register/logout)
│       ├── components/
│       │   ├── Navbar.jsx           # active-route highlighting, avatar/name chip -> Profile
│       │   ├── Avatar.jsx           # photo-or-initials avatar used in Navbar/Home/Profile
│       │   ├── ProtectedRoute.jsx   # Auth + RBAC route guard
│       │   ├── BarChart.jsx         # Lightweight dependency-free bar chart
│       │   ├── LineChart.jsx        # (M3) dependency-free SVG line chart (accuracy over time)
│       │   ├── LearningInsights.jsx # (M3) overall accuracy/attempts + AI feedback messages
│       │   ├── WeakAreas.jsx        # (M3) per-gesture accuracy table with skill-level pills
│       │   ├── Recommendations.jsx  # (M3) practice-count cards + trend/forecast
│       │   ├── LearningPlan.jsx     # (M3) numbered "today's plan"
│       │   ├── PerformanceTrend.jsx # (M3) accuracy-over-time chart + trend/forecast summary
│       │   └── AssessmentReport.jsx # (M3) generate/view/download the Assessment Report
│       ├── pages/
│           ├── Home.jsx           # attractive landing page: hero, welcome-back stats, feature grid, "how it works"
│           ├── Login.jsx          # Login + Register tabs
│           ├── Dashboard.jsx      # KPIs + gesture stats (M2) + AI feedback/weak areas/plan (M3)
│           ├── Profile.jsx        # app-style profile: photo/name header + collapsible Settings sections
│           ├── DatasetExplorer.jsx
│           ├── GesturePractice.jsx# (M2) webcam capture, landmark overlay, live scoring
│           ├── Certifications.jsx # (M4) eligibility checklist, issue/download/verify/print certs
│           ├── Reports.jsx        # (M4) tabbed Reports & Export System
│           └── AdminPanel.jsx
│
├── docs/
│   ├── architecture.md                        # System architecture (Milestone 1 base)
│   ├── wireframes.md                          # Text/ASCII wireframes for every M1 screen
│   ├── workflow.md                            # Sign language learning workflow design
│   ├── milestone2_gesture_engine.md           # Full Milestone 2 design writeup
│   ├── milestone3_learning_intelligence.md    # Full Milestone 3 design writeup
│   └── milestone4_certification_reporting.md  # Full Milestone 4 design writeup
│
├── docker-compose.yml             # (M4) brings up backend + frontend together
├── .gitignore
└── README.md
```

---

## 2. Scope Covered

### Milestone 1 (Week 1 & 2) — Project Initialization, Design Process & Core Setup

| # | Task | Status | Where it lives |
|---|------|--------|-----------------|
| 1 | Define project objectives & sign language learning workflow | ✅ | `docs/workflow.md` |
| 2 | Design system architecture & database schema | ✅ | `docs/architecture.md`, `backend/database/schema.sql` |
| 3 | Create UI wireframes & workflow planning | ✅ | `docs/wireframes.md` |
| 4 | Plan learner dashboard layout | ✅ | `docs/wireframes.md`, `frontend/src/pages/Dashboard.jsx` |
| 5 | Setup frontend (React) & backend (FastAPI) environments | ✅ | `frontend/`, `backend/main.py` |
| 6 | Configure backend routes | ✅ | `backend/routes/`, `backend/auth/routes.py` |
| 7 | Connect database | ✅ | `backend/database/db.py` |
| 8 | Implement authentication (JWT) & role-based access control | ✅ | `backend/auth/security.py`, `backend/deps.py`, `frontend/src/components/ProtectedRoute.jsx` |
| 9 | Build Login and Registration UI | ✅ | `frontend/src/pages/Login.jsx` |
| 10 | Build learner profile management workflows | ✅ | `backend/routes/profile.py`, `frontend/src/pages/Profile.jsx` — photo upload, editable display name, learning preferences, password change |
| 11 | Design learner profile screens | ✅ | `frontend/src/pages/Profile.jsx` — app-style header (photo/name/role) + collapsible Settings sections |
| 12 | Download / organize sign-language datasets | ✅ | `backend/datasets/dataset_downloader.py` |
| 13 | Explore dataset structures & analyze labels/formats | ✅ | `backend/datasets/dataset_explorer.py`, `frontend/src/pages/DatasetExplorer.jsx` |
| 14 | Begin preprocessing | ✅ | `backend/datasets/preprocessing.py` |
| 15 | Integrate sign language datasets into the platform | ✅ | `backend/routes/datasets.py`, `frontend/src/pages/DatasetExplorer.jsx` |
| 16 | Prepare documentation | ✅ | `docs/`, this README |

> **Profile & Home redesign:** the Home page is now a full landing/feature
> hub (hero, a "welcome back" stats strip for logged-in users, a feature
> grid linking to every part of the app, and a "How It Works" section), and
> the Profile page now looks like a normal app profile — a header card with
> an editable photo (`PUT /api/profile/identity`) and display name, and a
> collapsible **Settings** area below it (Learning Preferences, Account &
> Security — including a real change-password flow via
> `POST /api/auth/change-password`, and read-only Account Info). Photos are
> resized client-side to ≤300px and stored as a base64 thumbnail on the
> `learner_profiles` row — no object storage/S3 needed for this scale.

### Milestone 2 (Week 3 & 4) — Gesture Recognition Engine, Hand Tracking & Accuracy Assessment

| # | Task | Status | Where it lives |
|---|------|--------|-----------------|
| 1 | Implement gesture recognition engine | ✅ | `backend/gesture/classifier.py` |
| 2 | Build hand tracking workflows | ✅ | `backend/gesture/landmarks.py` (MediaPipe Hands) |
| 3 | Develop sign assessment models | ✅ | `backend/gesture/accuracy.py` |
| 4 | Create accuracy evaluation systems | ✅ | `/api/gesture/assess`, `gesture_attempts` DB table |
| 5 | Generate assessment reports | ✅ | `/api/gesture/history`, `/api/gesture/stats`, Dashboard integration |

**Full design rationale for Milestone 2 — including why a rule-based
classifier was used instead of a trained CNN, and the exact upgrade path —
is in [`docs/milestone2_gesture_engine.md`](docs/milestone2_gesture_engine.md).
Read that before assuming this recognizes the full ASL alphabet; it currently
recognizes 5 clearly-distinguishable hand shapes (Open Palm, Fist, Pointing,
Peace, Thumbs Up), each tied to a related ASL sign.**

### Milestone 3 (Week 5 & 6) — AI Feedback & Learning Intelligence Engine

| # | Task | Status | Where it lives |
|---|------|--------|-----------------|
| 1 | Implement feedback engine | ✅ | `backend/intelligence/feedback.py` |
| 2 | Build learning analytics workflows | ✅ | `backend/intelligence/analytics.py` (pandas + scikit-learn trend) |
| 3 | Develop recommendation engine | ✅ | `backend/intelligence/recommendations.py` (+ scikit-learn trend) |
| 4 | Generate personalized learning plans | ✅ | `backend/intelligence/learning_plan.py` |
| 5 | Create learner performance dashboard | ✅ | `frontend/src/pages/Dashboard.jsx` + `PerformanceTrend`, `LearningInsights`, `WeakAreas`, `Recommendations`, `LearningPlan` |
| 6 | Generate assessment reports | ✅ | `backend/intelligence/report.py`, `/api/intelligence/report`, `/api/intelligence/report/download`, `AssessmentReport.jsx` |
| 7 | Integrate AI feedback & learning intelligence end-to-end | ✅ | `/api/intelligence/summary` (single call bundling all of the above), Dashboard's "AI Feedback & Learning Intelligence" section |

Flow: **Milestone 2 assessment results → stored in `gesture_attempts` →
Learning Analytics → weak-area identification → AI Feedback Engine →
Recommendation Engine → Personalized Learning Plan → Assessment Report →
Learner Performance Dashboard.**
Every number is derived live from that learner's own logged practice
attempts — nothing is hard-coded per user. The dashboard also plots
**accuracy over time** (all attempts, chronological) with a scikit-learn
trend/forecast, so it's a genuine *performance* view, not just a snapshot.
Full design rationale, the exact data flow, and a worked example are in
[`docs/milestone3_learning_intelligence.md`](docs/milestone3_learning_intelligence.md).

### Milestone 4 (Week 7 & 8) — Certification, Testing & Deployment

| # | Task | Status | Where it lives |
|---|------|--------|-----------------|
| 1 | Implement certification workflows | ✅ | `backend/certification/rules.py`, `backend/routes/certification.py`, `frontend/src/pages/Certifications.jsx` |
| 2 | Build reporting modules | ✅ | `backend/reporting/reports.py`, `backend/routes/reports.py`, `frontend/src/pages/Reports.jsx` |
| 3 | Add analytics dashboards | ✅ | Reports page's "Class Overview" tab, Certifications page's "Certification Monitoring" section (Instructor/Admin) |
| 4 | Implement testing and validations | ✅ | `backend/tests/` — 9 automated pytest tests, run against an isolated temp DB |
| 5 | Docker containerization | ✅ | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` |
| 6 | Production deployment | ✅ | `docker compose up --build` brings up both services together |
| 7 | Documentation and user guides | ✅ | `docs/milestone4_certification_reporting.md` + this README |

Certificates (**Beginner / Intermediate / Advanced / Professional**) are
issued only when a learner's *live* analytics clear that level's
requirements (minimum attempts, minimum accuracy, minimum distinct
gestures, and — for Advanced/Professional — zero remaining weak areas).
Every certificate gets a unique verification code checkable at
`/api/certification/verify/{code}` with **no login required**. Reports are
exportable as CSV (Excel/Sheets-compatible); certificates additionally
support a browser-native "Print / Save as PDF" view. Full design rationale
is in [`docs/milestone4_certification_reporting.md`](docs/milestone4_certification_reporting.md).

---

## 3. Setup & Run

Two ways to run this: **locally** (two terminals) or **with Docker**
(one command). Both are fully supported.

### Option A — Local (two terminals)

#### Backend (FastAPI)

```bash
cd backend

# 1. Create & activate a virtual environment (recommended)
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) generate the bundled synthetic sample dataset if it's missing
python datasets/generate_sample_data.py

# 4. Run the API server
uvicorn main:app --reload --port 8000
```

The SQLite database (`backend/platform.db`) and its tables are created
automatically on first startup. Interactive API docs are available at
**http://localhost:8000/docs** — including the `/api/intelligence/*`
(Milestone 3) and `/api/certification/*` + `/api/reports/*` (Milestone 4)
routes.

#### Frontend (React + Vite)

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. (Optional) point the frontend at a different backend URL
cp .env.example .env   # edit VITE_API_BASE_URL if not using http://localhost:8000

# 3. Run the dev server
npm run dev
```

Open **http://localhost:5173** in your browser. The frontend expects the
backend to be running at `http://localhost:8000` by default (see
`frontend/.env.example`).

> **Webcam note (Milestone 2):** browsers only allow camera access
> (`getUserMedia`) on `localhost`/`127.0.0.1` or over HTTPS. Running both
> servers locally as shown above works out of the box; if you deploy this
> anywhere else, the frontend needs to be served over HTTPS for the Gesture
> Practice page's camera to work.

### Option B — Docker (one command)

```bash
docker compose up --build
```

- Frontend: **http://localhost:5173**
- Backend: **http://localhost:8000** (docs at `/docs`)

The SQLite database persists in a named Docker volume (`backend_data`), so
stopping and restarting the containers keeps your data; `docker compose
down -v` wipes it. See §6 and
[`docs/milestone4_certification_reporting.md`](docs/milestone4_certification_reporting.md)
for details on what each container does.

> **Note:** the Docker images could not be build-tested in the environment
> this was assembled in (no Docker daemon / registry access available
> there) — the Dockerfiles and compose file follow standard, well-tested
> patterns, but please do a `docker compose up --build` on your own machine
> before a live demo to confirm it pulls cleanly.

### Running the test suite

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

9 tests cover certification eligibility/issuance/verification and every
`/api/reports/*` endpoint, including role-based-access checks. Each test
run uses its own temporary SQLite file — your real `platform.db` is never
touched.

### Default roles available at registration
- `Learner`
- `Instructor`
- `Accessibility Trainer`
- `Administrator`

> Tip: register your first account as **Administrator** to unlock the Admin
> Panel (`/admin` route), which is protected by role-based access control on
> both the frontend (route guard) and backend (API dependency). Register a
> second account as **Instructor** to see the Certification Monitoring and
> Class Overview views, which are hidden from Learners.

---

## 4. Datasets

Milestone 1 covers **downloading, organizing, and exploring** the datasets
recommended in the project plan (actual gesture-recognition model training is
Milestone 2+):

- ASL Alphabet Dataset
- Sign Language MNIST Dataset
- WLASL (Word-Level American Sign Language) Dataset
- RWTH-PHOENIX Dataset

Because these datasets are large and hosted on Kaggle/academic mirrors,
`backend/datasets/dataset_downloader.py` is written as a **ready-to-run
downloader** (using the `kaggle` CLI/API) that you run locally with your own
Kaggle API credentials — it is not called automatically by the API server. To
let you try the platform immediately without any downloads, a small
**synthetic sample dataset** is included under `backend/datasets/sample_data/`
and the Dataset Explorer page works against it out of the box.

Downloaded real datasets should be placed under `backend/datasets/raw/<name>/`
(one subfolder per class label) — they'll automatically show up as options in
the Dataset Explorer's dataset picker.

---

## 5. Tech Stack

- **Frontend:** React 18, React Router, Vite (no UI framework — custom CSS), browser `getUserMedia` + `<canvas>` for webcam capture and landmark overlay
- **Backend:** FastAPI, Uvicorn, Pydantic
- **Auth:** JWT (PyJWT) + salted SHA-256 password hashing
- **Database:** SQLite (via Python's built-in `sqlite3`)
- **Dataset tooling:** Pillow, NumPy
- **Gesture Recognition & Hand Tracking (Milestone 2):** MediaPipe Hands (`mediapipe==0.10.14`, legacy `solutions` API), geometric finger-state classification (see `docs/milestone2_gesture_engine.md`)
- **AI Feedback & Learning Intelligence (Milestone 3):** pandas (learning analytics / weak-area aggregation), scikit-learn (`LinearRegression` for per-gesture and overall performance-trend forecasting) — see `docs/milestone3_learning_intelligence.md`
- **Certification & Reporting (Milestone 4):** rule-based eligibility engine, `hashlib`/`secrets` for verification codes, Python's built-in `csv` module for Excel-compatible exports — see `docs/milestone4_certification_reporting.md`
- **Testing (Milestone 4):** pytest + FastAPI's `TestClient`
- **Deployment (Milestone 4):** Docker (multi-stage builds), nginx (serving the built frontend), Docker Compose
- **Charts:** dependency-free `BarChart` / `LineChart` components (no external chart library added)

This matches the overall project tech stack (FastAPI/React/PostgreSQL/
TensorFlow/MediaPipe/Pandas/Scikit-learn etc.) at a scale appropriate for a
student/portfolio deliverable. A larger-scale production version would swap
SQLite for PostgreSQL, add the remaining microservices/AI layers (a trained
CNN/LSTM gesture classifier, a learned recommendation model), and deploy the
containers here to a managed cloud service (AWS ECS / Azure Container
Apps) instead of a single Docker Compose host.

---

## 6. What's intentionally out of scope

See each milestone doc's own "Deliberately out of scope" section for the
full reasoning, but in short:

- A trained CNN/LSTM gesture classifier (Milestone 2 uses an explainable
  geometric rule-based classifier by design)
- A learned/ML-based recommendation model (Milestone 3's recommendation
  engine is threshold-based; the trend/forecast component is the first
  real ML piece)
- Certificate revocation from the Admin UI (the DB/API support it; no
  button is wired up yet)
- Binary PDF/XLSX generation on the backend (handled via CSV + browser
  print-to-PDF instead — see `docs/milestone4_certification_reporting.md` §3)
- Standing up real managed cloud infrastructure (the Docker Compose setup
  here is deployment-ready but doesn't push to a live AWS/Azure account)
