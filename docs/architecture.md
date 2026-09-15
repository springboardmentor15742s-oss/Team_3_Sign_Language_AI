# System Architecture — Milestone 1 Slice (React + FastAPI)

## 1. Full-project architecture (target, per project plan)

The overall platform (from the Infosys project brief) is designed as:

- **Clients:** Web App, Mobile App, Instructor Portal, Admin Dashboard, Reports & Analytics
- **API Gateway:** FastAPI (routing, auth, rate limiting, validation, load balancing, CORS, logging)
- **Microservices layer:** User/Profile, Course/Content, Video Management, Pose & Hand Tracking,
  Gesture Recognition, Accuracy Assessment, AI Feedback & Correction, Learning Intelligence,
  Assessment & Quiz, Performance Scoring, Risk & Performance, Certification, Notification
- **AI/ML & Intelligence layer:** Gesture Classification (CNN), Sequence Recognition (LSTM/Transformer),
  Accuracy Evaluation, Mistake Detection, Learning Analytics, NLP Feedback Generation, Recommendation Engine
- **Data processing & streaming layer:** Video upload/ingestion, frame extraction/normalization,
  real-time WebSocket streaming, feature extraction, inference & scoring, caching
- **Data layer:** PostgreSQL (relational), MongoDB (documents/content), Redis (cache/queue),
  Cloud storage (video/certs), Data warehouse (analytics), Vector DB (embeddings)
- **Cross-cutting:** Monitoring & logging, security & compliance, external services
  (cloud storage, CDN, AI/ML model hosting, email, push notifications, auth provider, payments)

## 2. Milestone 1 architecture (this deliverable)

This build replaces the earlier Streamlit prototype with a **real two-tier
web app** — a React single-page app talking to a FastAPI JSON API over
HTTP — which is a much closer match to the full target architecture
(API Gateway + Microservices + clients) than the previous single-process
Streamlit build.

```
┌─────────────────────────────┐
│   React SPA (Vite)           │   <- frontend/  (port 5173 in dev)
│  React Router + Context API  │
│  fetch()-based API client    │
└───────────────┬──────────────┘
                │  HTTPS / JSON, Authorization: Bearer <JWT>
┌───────────────▼──────────────┐
│   FastAPI application         │   <- backend/  (port 8000)
│  main.py + routers            │
│  ┌──────────────────────────┐ │
│  │ /api/auth   (register,   │ │
│  │   login, me)              │ │
│  │ /api/profile (CRUD)       │ │
│  │ /api/dashboard (KPIs)     │ │
│  │ /api/datasets (explore,   │ │
│  │   preview, preprocess)    │ │
│  │ /api/admin  (users, RBAC) │ │
│  └──────────────────────────┘ │
│  deps.py: JWT auth + RBAC     │
│  guards on every route        │
└───────────────┬──────────────┘
                │
┌───────────────▼──────────────┐
│      Data Access Layer        │
│  database/db.py               │
└───────────────┬──────────────┘
                │
┌───────────────▼──────────────┐
│         SQLite DB             │   <- stand-in for PostgreSQL in
│  users / learner_profiles /   │      the full architecture
│  practice_history / dataset_log│
└────────────────────────────────┘

     (separate, offline)
┌────────────────────────────────┐
│   backend/datasets/ tools       │
│  dataset_downloader.py          │  -> pulls from Kaggle (needs
│  dataset_explorer.py            │     internet + Kaggle API key,
│  preprocessing.py               │     run outside the sandbox)
│  sample_data/ (synthetic demo)  │
└────────────────────────────────┘
```

### Why React + FastAPI (vs. the earlier Streamlit build)?
This matches the target tech stack from the project brief (`React.js` +
`FastAPI` + `PostgreSQL`) far more closely:
- **Real REST API** the eventual mobile app / instructor portal / admin
  dashboard clients can also call — not something tightly coupled to a
  single Python process like Streamlit was.
- **JWT-based stateless auth**, matching "JWT authentication" from Module 1
  of the task list, instead of an in-memory Streamlit session.
- **Clear separation of concerns**: `backend/` can be containerized and
  deployed independently of `frontend/`, as called for in Milestone 4
  ("Docker containerization", "Frontend and backend integration").

SQLite is still used in place of PostgreSQL for Milestone 1 simplicity —
`database/db.py` is a thin, swappable data-access layer, so upgrading to
PostgreSQL later mainly means changing the connection string and query
style (or moving to SQLAlchemy), not rewriting the routes.

## 3. Database Schema (Milestone 1)

See `backend/database/schema.sql` for the authoritative schema. Summary:

| Table | Purpose |
|---|---|
| `users` | Account credentials + role (RBAC) |
| `learner_profiles` | Learning level, preferred language, goals, bio |
| `practice_history` | Placeholder for Milestone-2 practice-session logging |
| `dataset_log` | Audit trail of dataset explore/preprocess actions |

## 4. Authentication & Role-Based Access Control (RBAC)

- **Password storage:** salted SHA-256 hash (`backend/auth/security.py`)
- **Sessions:** signed JWTs (`PyJWT`), issued on login, sent as
  `Authorization: Bearer <token>` on every subsequent request
- **RBAC enforcement:** `backend/deps.py` exposes `get_current_user()` and
  `require_roles(*roles)` FastAPI dependencies, used to protect routes
  (e.g. `/api/admin/*` requires the `Administrator` role)
- **Frontend enforcement:** `frontend/src/components/ProtectedRoute.jsx`
  redirects unauthenticated users to `/login` and shows an access-denied
  message for role-restricted pages (e.g. `/admin`)

Four roles, matching the project brief: **Learner**, **Instructor**,
**Accessibility Trainer**, **Administrator**.

- **Two-way login UI:** `frontend/src/pages/Login.jsx` presents two portals
  — "Learner / Staff" (login + self-registration, with `Administrator`
  removed from the registration role dropdown) and "Administrator"
  (login-only). Administrator accounts are never self-registered; they're
  created by promoting an existing user's role from the Admin Panel. Each
  portal checks the returned user's role after a successful login and
  rejects with a clear message (logging the session back out) if the
  account's role doesn't match the portal used — e.g. an Administrator
  account signing in via the Learner/Staff tab, or a non-admin account
  signing in via the Administrator tab. This check is client-side only,
  layered on top of the server-side `require_roles()` RBAC enforcement
  that already protects every admin-only route.

## 5. API Surface (Milestone 1)

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/api/auth/register` | — | Create account |
| POST | `/api/auth/login` | — | Log in, get JWT |
| GET | `/api/auth/me` | ✅ | Current user info |
| GET | `/api/profile` | ✅ | Get learner profile |
| PUT | `/api/profile` | ✅ | Create/update learner profile |
| GET | `/api/dashboard` | ✅ | KPIs + recent activity |
| POST | `/api/dashboard/log-activity` | ✅ | Demo activity logging |
| GET | `/api/datasets/recommended` | — | Recommended datasets list |
| GET | `/api/datasets/list` | — | Locally available dataset folders |
| GET | `/api/datasets/{name}/structure` | ✅ | Label distribution |
| GET | `/api/datasets/{name}/preview` | ✅ | Sample image URLs per class |
| GET | `/api/datasets/{name}/image/{cls}/{file}` | — | Serve a sample image |
| GET | `/api/datasets/{name}/format-report` | ✅ | Image dimension/format report |
| POST | `/api/datasets/{name}/preprocess` | ✅ | Resize/normalize & save |
| GET | `/api/datasets/log` | ✅ | Dataset action audit log |
| GET | `/api/admin/users` | ✅ (Admin) | List all users |
| PUT | `/api/admin/users/{id}/role` | ✅ (Admin) | Change a user's role |
| PUT | `/api/admin/users/{id}/active` | ✅ (Admin) | Activate/deactivate a user |

Interactive Swagger docs are auto-generated by FastAPI at
`http://localhost:8000/docs` when the backend is running.
