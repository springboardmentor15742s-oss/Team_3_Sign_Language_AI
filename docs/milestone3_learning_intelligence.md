# Milestone 3 — AI Feedback & Learning Intelligence Engine

Week 5 & 6 deliverable, built on top of the Milestone 1 + 2 base. Nothing in
Milestone 2 was modified — Milestone 3 is a new read-side layer that
consumes the `gesture_attempts` rows Milestone 2 already logs.

## 1. What's implemented

| Roadmap task | Status | Where |
|---|---|---|
| Implement feedback engine | ✅ | `backend/intelligence/feedback.py` |
| Build learning analytics workflows | ✅ | `backend/intelligence/analytics.py` |
| Develop recommendation engine | ✅ | `backend/intelligence/recommendations.py` |
| Generate personalized learning plans | ✅ | `backend/intelligence/learning_plan.py` |
| Create learner performance dashboard | ✅ | `frontend/src/pages/Dashboard.jsx` + `PerformanceTrend`, `LearningInsights`, `WeakAreas`, `Recommendations`, `LearningPlan` components |
| Generate assessment reports | ✅ | `backend/intelligence/report.py`, `/api/intelligence/report(/download)`, `AssessmentReport.jsx` |
| Integrate AI feedback & learning intelligence | ✅ | `/api/intelligence/summary` bundles the whole pipeline in one call for the dashboard |

Outcome delivered: a functional AI feedback engine, a working learning
analytics/weak-area pipeline, personalized (not one-size-fits-all)
recommendations and learning plans, a performance dashboard with an
accuracy-over-time trend chart, and on-demand assessment reports — all
visible on and driven from the Learner Performance Dashboard.

## 2. The Milestone 3 flow

```
Milestone 2 Assessment Results   (gesture_attempts rows: target, detected,
        |                         hand-shape accuracy, position accuracy,
        v                         overall accuracy, feedback — logged by
   Store Results                  routes/gesture.py on every /assess call)
        |
        v
 Learning Analytics        backend/intelligence/analytics.py
        |                  pandas groupby over every attempt -> overall
        v                  accuracy, per-gesture accuracy, skill level
  Find Weak Areas          < 70% Needs Improvement / 70-85% Developing / >85% Good
        |
        v
  Feedback Engine          backend/intelligence/feedback.py
        |                  strengths / weaknesses + most common corrective
        v                  note per weak gesture, mined from real feedback text
 Recommendation Engine     backend/intelligence/recommendations.py
        |                  practice count per weak gesture (5 / 3 / 2) +
        v                  scikit-learn linear-regression trend/forecast
 Personalized Learning Plan  backend/intelligence/learning_plan.py
        |                    orders recommendations into "today's plan"
        v
   Learner Dashboard        frontend Dashboard.jsx + LearningInsights /
                             WeakAreas / Recommendations / LearningPlan
```

## 3. Where the "AI" actually is

Nothing here is hard-coded per learner. Every number traces back to that
learner's own `gesture_attempts` rows:

```
Database                    Analytics                Weak Area        Recommendation
Peace: 60, 62, 58, 65   ->  Average = 61.25%     ->  Peace        ->  Practice Peace more
```

`analytics.compute_analytics()` is the single source of truth — it's the
only place that reads the database and does the pandas aggregation.
`feedback.py`, `recommendations.py`, and `learning_plan.py` all take its
output as their only input, so the whole chain stays consistent and there's
one place to change the weak-area thresholds.

**Performance forecasting** (the roadmap's Scikit-learn line item):
`recommendations._trend_for_gesture()` fits a `sklearn.linear_model.
LinearRegression` over a gesture's accuracy-per-attempt once there are ≥3
logged attempts on it, and reports whether the learner is `improving`,
`declining`, or `steady`, plus a predicted next-attempt accuracy. With fewer
than 3 attempts it returns `None` rather than fabricating a trend from too
little data.

## 4. Backend layout added

```
backend/
├── intelligence/
│   ├── __init__.py
│   ├── analytics.py        # Learning Analytics (pandas)
│   ├── feedback.py         # AI Feedback & Correction Engine
│   ├── recommendations.py  # Recommendation Engine (+ scikit-learn trend)
│   └── learning_plan.py    # Personalized Learning Plan
└── routes/
    └── intelligence.py     # /api/intelligence/* endpoints
```

`database/db.py` gained one new read helper, `get_all_gesture_attempts()`
— the full, chronologically-ordered attempt history a user needs for
analytics and trend fitting (the existing `get_gesture_history()` stays
newest-first and limited, for the Dashboard's recent-activity feed).

No schema changes were needed: Milestone 2's `gesture_attempts` table
already had everything Milestone 3 needed to read.

## 5. API endpoints

All under `/api/intelligence`, all JWT-protected (same `get_current_user`
dependency as every other route), all scoped to the calling learner:

| Endpoint | Returns |
|---|---|
| `GET /api/intelligence/analytics` | Overall/best accuracy, per-gesture accuracy + skill level |
| `GET /api/intelligence/weak-areas` | `weak_areas` / `strong_areas` split out of analytics |
| `GET /api/intelligence/feedback` | AI feedback summary, strengths, weaknesses, common mistake per weak gesture |
| `GET /api/intelligence/recommendations` | Per-gesture practice count + reason + trend/forecast |
| `GET /api/intelligence/learning-plan` | Ordered "today's plan" built from recommendations |
| `GET /api/intelligence/performance-trend` | Chronological accuracy-per-attempt points + overall trend/forecast |
| `GET /api/intelligence/report` | Full Assessment Report (JSON) — logs a `assessment_reports` row |
| `GET /api/intelligence/report/download` | Same report, rendered as a downloadable `.txt` file |
| `GET /api/intelligence/report/history` | Past report-generation events for this learner |
| `GET /api/intelligence/summary` | Analytics + feedback + recommendations + learning plan + performance trend bundled in one response — what the Dashboard actually calls |

## 6. Frontend layout added

```
frontend/src/
├── pages/
│   └── Dashboard.jsx            # updated: fetches intelligence summary
└── components/
    ├── LearningInsights.jsx     # overall accuracy / attempts / best + AI feedback messages
    ├── WeakAreas.jsx            # per-gesture accuracy table with level pills
    ├── Recommendations.jsx      # practice-count cards + trend line
    └── LearningPlan.jsx         # numbered "today's plan"
```

`api.js` gained matching client methods (`getIntelligenceSummary`,
`getAnalytics`, `getWeakAreas`, `getFeedback`, `getRecommendations`,
`getLearningPlan`). The Dashboard fetches `/api/dashboard` and
`/api/intelligence/summary` in parallel on load.

## 7. Worked example (matches the roadmap's own walkthrough)

Seed a learner with these gesture attempts and the pipeline produces:

```
Open Palm  → 90, 92, 94, 91   (avg 91.8% — Good)
Peace      → 58, 60, 62, 65   (avg 61.2% — Needs Improvement)
Pointing   → 60, 65, 63, 68   (avg 64.0% — Needs Improvement)
```

`GET /api/intelligence/summary` returns:

- **Feedback:** "You are performing well on Open Palm. You need more
  practice with Peace / Victory Sign, Pointing (Index Up). Peace / Victory
  Sign: focus on this — curl your ring finger into your palm. ..."
- **Recommendations:** Peace → practice 5×, Pointing → practice 5×,
  Open Palm → practice 2× (maintenance), each with a trend/forecast.
- **Learning Plan:** "Practice Peace / Victory Sign and Pointing (Index Up)
  today." — an ordered 3-item plan, weakest gesture first.

This was verified end-to-end against the running FastAPI app (register →
login → seed attempts → call every `/api/intelligence/*` endpoint) before
this build was packaged.

## 8. Deliberately out of scope for Milestone 3

- **Real-time (in-session) feedback while practicing** — the current
  feedback engine analyzes the *stored* attempt history, not a live video
  stream; Milestone 2's per-attempt feedback already covers the immediate,
  in-the-moment correction.
- **A trained recommendation model** — the practice-count logic is
  threshold-based (5 / 3 / 2 reps) by design, for the same explainability
  reason Milestone 2 uses a rule-based classifier instead of a trained CNN.
  The scikit-learn trend/forecast is the first real ML component; a
  learned recommender is a natural Milestone 4+ upgrade once there's a
  larger cross-learner dataset to train on.
- **Certification workflows, PDF/Excel export, deployment** — these are
  now implemented in Milestone 4; see
  `docs/milestone4_certification_reporting.md`.
