# Sign Language Learning Workflow — Design (Milestone 1)

## 1. Project Objective (recap)

Build an AI-powered platform that helps users learn sign language through
interactive lessons, real-time gesture recognition, AI-driven feedback, and
performance assessments — for students, hearing-impaired individuals,
educators, language trainers, schools, and accessibility organizations.

## 2. End-to-end learner workflow

```
1. Register / Login
        │
        ▼
2. Create Learner Profile
   (learning level, preferred sign language, learning goals)
        │
        ▼
3. Browse recommended course categories
   (Beginner → Intermediate → Advanced → Everyday/Educational/Professional)
        │
        ▼
4. Practice signs on camera            <- Milestone 2 (Gesture Recognition Engine)
        │
        ▼
5. Receive real-time accuracy scoring   <- Milestone 2 (Accuracy Assessment Engine)
   & AI feedback / correction           <- Milestone 3 (AI Feedback Engine)
        │
        ▼
6. Track progress on Learner Dashboard
   (skill mastery, weak areas, recommendations) <- Milestone 3 (Learning Intelligence)
        │
        ▼
7. Take practice quizzes & certification exams  <- Milestone 4
        │
        ▼
8. Download performance / certification reports <- Milestone 4
```

## 3. What Milestone 1 delivers from this workflow

Steps **1, 2, and 3 (partially)** are implemented end-to-end in this build:

- **Register / Login** — full working JWT-based auth with role selection (RBAC),
  React `Login.jsx` page ↔ FastAPI `/api/auth/*` routes
- **Learner Profile** — learning level, preferred language, and goals are
  captured client-side (`Profile.jsx`) and persisted via `/api/profile`
- **Course browsing** — not yet built (Milestone 1 focuses on *datasets* that
  will power course content generation, not the course catalog UI itself,
  which is a Week 3+ deliverable per the project plan)
- **Dashboard** — the layout/wireframe is implemented with live KPIs
  (profile completeness, goals, logged activities) pulled from
  `/api/dashboard`, and clearly marked placeholders for gesture-accuracy
  metrics that populate starting Milestone 2

## 4. Roles and their journeys

| Role | Milestone 1 capabilities |
|---|---|
| **Learner** | Register, log in, manage profile, view dashboard |
| **Instructor** | Register, log in (dashboard/course-authoring views ship in later milestones) |
| **Accessibility Trainer** | Register, log in (analytics views ship in later milestones) |
| **Administrator** | All of the above + Admin Panel: manage users/roles, view dataset integration log |

## 5. Data flow for dataset integration (this milestone)

```
Kaggle / academic dataset sources
        │  (backend/datasets/dataset_downloader.py — run locally
        │   with a Kaggle API key; not executed by the API server)
        ▼
backend/datasets/raw/<dataset_name>/<class_label>/<images>
        │  (dataset_explorer.py logic, exposed via
        │   GET /api/datasets/{name}/structure & /format-report)
        ▼
React "Dataset Explorer" page (visual inspection, format report,
image preview served from GET /api/datasets/{name}/image/{cls}/{file})
        │  (preprocessing.py logic, exposed via
        │   POST /api/datasets/{name}/preprocess)
        ▼
backend/datasets/processed/<dataset_name>/<class_label>/<images>
        →  ready for Milestone-2 model training
```

Every explore/preprocess action is written to the `dataset_log` table via
the backend, and surfaced on both the React Dataset Explorer page and the
Admin Panel (`GET /api/datasets/log`) for auditability.
