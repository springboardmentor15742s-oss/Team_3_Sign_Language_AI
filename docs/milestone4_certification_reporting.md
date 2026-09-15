# Milestone 4 — Certification, Testing & Deployment

Week 7 & 8 deliverable, built on top of Milestones 1–3. Nothing in the
earlier milestones was modified — Milestone 4 adds a new certification
layer and a reporting layer, both reading data that already exists
(`gesture_attempts` via `intelligence/analytics.py`), plus containerization
so the whole platform can be deployed with Docker.

## 1. What's implemented

| Roadmap task | Status | Where |
|---|---|---|
| Implement certification workflows | ✅ | `backend/certification/rules.py`, `backend/routes/certification.py` |
| Build reporting modules | ✅ | `backend/reporting/reports.py`, `backend/routes/reports.py` |
| Add analytics dashboards | ✅ | `Reports.jsx` (Class Overview tab), `Certifications.jsx` (Certification Monitoring) |
| Implement testing and validations | ✅ | `backend/tests/` (pytest, run against a temp SQLite DB) |
| Docker containerization | ✅ | `backend/Dockerfile`, `frontend/Dockerfile`, `docker-compose.yml` |
| Production deployment | ✅ | `docker-compose.yml` brings up both services together; see §6 |
| Documentation and user guides | ✅ | this file + updated root `README.md` |

## 2. Certification Workflows

`certification/rules.py` defines four levels — **Beginner, Intermediate,
Advanced, Professional** — matching the roadmap's Assessment Levels. Each
level has explicit, checkable requirements:

| Level | Min attempts | Min accuracy | Min distinct gestures | No weak areas? |
|---|---|---|---|---|
| Beginner | 5 | 60% | 3 | No |
| Intermediate | 15 | 75% | 5 | No |
| Advanced | 30 | 85% | 8 | Yes |
| Professional | 50 | 92% | 10 | Yes |

A certificate is **never manually approved** — `check_eligibility()` calls
Milestone 3's `compute_analytics()` at the moment of issue and only
inserts a row if every requirement is currently met. This means
eligibility can never drift out of sync with what the Dashboard shows,
and a learner can't be issued a certificate for a level they've since
regressed below.

Each certificate gets a unique, non-guessable `certificate_code` (e.g.
`SLP-ADV-3F91A0C2E1`) generated from a SHA-256 hash of the user, level,
timestamp, and a random salt — this is what `/api/certification/verify/
{code}` uses for public, no-login verification (so an employer or
instructor can confirm a certificate is genuine and still Active).

### Certification endpoints

| Endpoint | Auth | Returns |
|---|---|---|
| `GET /api/certification/eligibility` | Learner | Progress + pass/fail reasons for all 4 levels |
| `POST /api/certification/issue/{level}` | Learner | Issues a certificate if eligible (409 if already held, 400 with reasons if not eligible) |
| `GET /api/certification/my` | Learner | This learner's certificates |
| `GET /api/certification/{id}/download` | Owner / Instructor / Admin | Plain-text certificate file |
| `GET /api/certification/verify/{code}` | **Public** | `{valid, username, level, status, ...}` |
| `GET /api/certification/all` | Instructor / Accessibility Trainer / Administrator | Platform-wide certificate list ("Certification monitoring") |

## 3. Reporting Modules

Milestone 3 already produced one report type — the combined Assessment
Report (`intelligence/report.py`). Milestone 4's `reporting/reports.py`
adds the other report types the roadmap's "Reports & Export System" calls
for, all exportable as **CSV** (opens directly in Excel/Sheets — the
roadmap's "Excel export" outcome, without adding a binary/PDF dependency
to the backend):

| Report | Endpoint | Format |
|---|---|---|
| Learning Report | `GET /api/reports/learning` | JSON summary (accuracy, trend, breakdown) |
| Accuracy Report | `GET /api/reports/accuracy/csv` | CSV, one row per gesture |
| Progress Report | `GET /api/reports/progress/csv` | CSV, one row per attempt, chronological |
| Certification Report | `GET /api/reports/certification/csv` | CSV of this learner's certificates |
| Class Overview | `GET /api/reports/class-overview(/csv)` | Instructor/Admin only — one row per learner |

**PDF export** is handled on the frontend instead of the backend: the
Certifications page's "🖨️ Print / PDF" button opens a formatted,
print-ready certificate in a new tab and calls the browser's native print
dialog (`window.print()`), which every browser can "Save as PDF" from
directly — a real, working PDF export path without adding `reportlab`/
`weasyprint` as a backend dependency.

## 4. Frontend additions

```
frontend/src/
├── pages/
│   ├── Certifications.jsx   # eligibility checklist, issue/download/verify certs
│   └── Reports.jsx          # tabbed Reports & Export System (5–6 report types)
└── components/
    └── AssessmentReport.jsx # (Milestone 3, reused as the "Assessment Report" tab)
```

The Navbar gained **Certifications** and **Reports** links, and now uses
`NavLink` with an active-route underline instead of plain `Link`, so the
current page is visually obvious. Certificate cards render a live
checklist (✅/⬜ per requirement) driven directly by
`/api/certification/eligibility` — nothing is a static image or hard-coded
progress bar.

## 5. Testing

`backend/tests/test_milestone4.py` runs with `pytest` against a temporary
SQLite database (created fresh per test run, never touching
`platform.db`) and covers:

- registering/logging in a learner and logging gesture attempts
- certification eligibility becoming `True` only once thresholds are met
- issuing a certificate and rejecting a duplicate issue (`409`)
- public certificate verification
- every `/api/reports/*` endpoint, including the `403` a Learner gets on
  the Instructor-only `class-overview` endpoint

Run it with:

```bash
cd backend
pip install -r requirements.txt -r requirements-dev.txt
pytest -v
```

## 6. Docker & Deployment

Both services now have a `Dockerfile`, plus a root `docker-compose.yml`
that brings them up together:

```bash
docker compose up --build
```

- Backend container: Python 3.12-slim, installs `requirements.txt`,
  serves FastAPI via `uvicorn` on port `8000`. The SQLite database is
  written to a mounted volume (`backend_data`) so it survives container
  restarts.
- Frontend container: multi-stage build — `npm run build` in a Node
  builder stage, then the static `dist/` output is served by `nginx` on
  port `80` (mapped to host `5173` in compose, matching the local dev
  URL). `VITE_API_BASE_URL` is baked in at build time via a build arg.

This satisfies the roadmap's Docker containerization + production
deployment tasks with a config that works identically on a laptop or a
cloud VM (AWS/Azure) — `docker compose up` is the entire deployment step.

## 7. Deliberately out of scope for Milestone 4

- **A managed cloud deployment** (actually pushing containers to AWS ECS /
  Azure Container Apps, provisioning a managed Postgres, etc.) — the
  Docker Compose setup here is deployment-ready but stops short of
  standing up real cloud infrastructure, which needs live cloud
  credentials this environment doesn't have.
- **Revoking certificates from the UI** — the `certificates.status` column
  and DB layer support it (`'Revoked'`), but there's no admin action wired
  up yet to flip it; this is a natural next step for an Admin Panel
  extension.
- **Binary PDF/XLSX generation on the backend** — handled pragmatically via
  CSV (Excel-compatible) + browser print-to-PDF instead, per §3, to avoid
  a heavy new dependency for a "nice to have" format.
