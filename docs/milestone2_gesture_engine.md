# Milestone 2 — Gesture Recognition Engine, Hand Tracking & Accuracy Assessment

Week 3 & 4 deliverable, built on top of the Milestone 1 React + FastAPI base.

## 1. What's implemented

| Project-plan task | Status | Where |
|---|---|---|
| Implement gesture recognition engine | ✅ | `backend/gesture/classifier.py` |
| Build hand tracking workflows | ✅ | `backend/gesture/landmarks.py` (MediaPipe Hands) |
| Develop sign assessment models | ✅ | `backend/gesture/accuracy.py` |
| Create accuracy evaluation systems | ✅ | `/api/gesture/assess`, DB `gesture_attempts` table |
| Generate assessment reports | ✅ | `/api/gesture/history`, `/api/gesture/stats`, Dashboard integration |

## 2. Engine design

### Hand & Pose Tracking (`gesture/landmarks.py`)
Uses **MediaPipe Hands** (legacy `mediapipe.python.solutions` API — pinned
to `mediapipe==0.10.14` because that's the last release that bundles its
hand-landmark model *inside the pip package*. Newer MediaPipe releases moved
to the "Tasks" API, which needs to download a separate `.task` model file
from Google's CDN on first use — an extra runtime dependency we intentionally
avoid here). Detects **21 hand landmarks** per frame (wrist + 4 joints per
finger), matching the "Tracked Landmarks" list from the project brief.

### Gesture Recognition Engine (`gesture/classifier.py`)
Real gesture recognition for the full ASL alphabet needs a trained
CNN/LSTM/Transformer model on a labeled dataset (WLASL, ASL-Alphabet,
Sign-MNIST — already wired up for download/exploration in Milestone 1's
Dataset Explorer). That training run needs a GPU and the real dataset, which
this offline build doesn't have access to.

So Milestone 2 ships a **genuinely-working, rule-based geometric classifier**
instead: it computes which of the 5 fingers are extended vs. curled from the
real MediaPipe landmarks (using distance-from-wrist / distance-from-palm
heuristics — robust to hand rotation and left/right handedness), then
matches that 5-bit "finger state" against a small reference library of
clearly-distinguishable static hand shapes:

| Gesture | Related sign | Finger pattern (T-I-M-R-P) |
|---|---|---|
| Open Palm | ASL 'B' / Number 5 | 1-1-1-1-1 |
| Closed Fist | ASL 'A' / 'S' | 0-0-0-0-0 |
| Pointing | ASL 'D' / Number 1 | 0-1-0-0-0 |
| Peace / Victory | ASL 'V' / Number 2 | 0-1-1-0-0 |
| Thumbs Up | Approval sign | 1-0-0-0-0 |

This is an honest scope decision: a finger up/down heuristic **cannot**
reliably distinguish handshapes that differ mainly by curvature or thumb
placement (e.g. ASL 'C' vs 'O' vs 'E'), so rather than ship an inaccurate
26-letter "recognizer", Milestone 2 ships a small, *actually accurate* set —
validated with synthetic landmark unit tests in addition to the live
MediaPipe pipeline (see `backend/gesture/` — feel free to inspect the logic).

**Upgrade path (Milestone 3+):** swap `classify_by_fingerstate()` for a
trained model's `.predict()` call. The API contract
(`/api/gesture/detect`, `/api/gesture/assess`) doesn't need to change —
only what's inside `classifier.py`.

### Sign Accuracy Assessment Engine (`gesture/accuracy.py`)
For a chosen target gesture, scores a submitted frame on:
- **Hand Shape Accuracy** — % of fingers in the correct extended/curled state
- **Position Accuracy** — is the hand fully in frame and reasonably sized/centered
- **Overall Accuracy** — weighted combination of the above + MediaPipe's
  handedness-detection confidence

...and generates **per-finger, corrective feedback** ("Extend your index
finger further", "Curl your pinky finger into your palm") — a lightweight
preview of the full AI Feedback & Correction Engine that's the centerpiece
of Milestone 3.

*(Motion Accuracy and Gesture Timing — also listed under "Assessment
Metrics" in the project plan — require a video **sequence**, not a single
static frame, and are natural additions once continuous webcam capture /
WebSocket streaming is added in a later milestone.)*

## 3. API additions

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/api/gesture/library` | — | Reference gesture library (for "how to sign X" UI) |
| GET | `/api/gesture/hand-connections` | — | Landmark index pairs, for drawing the hand skeleton |
| POST | `/api/gesture/detect` | ✅ | Upload a frame → landmarks + recognized gesture (no target) |
| POST | `/api/gesture/assess` | ✅ | Upload a frame + target gesture → full accuracy assessment, logs attempt |
| GET | `/api/gesture/history` | ✅ | Past practice attempts |
| GET | `/api/gesture/stats` | ✅ | Aggregate accuracy stats (also surfaced on the Dashboard) |

`GET /api/dashboard` now also returns a `gesture_stats` block, and the React
Dashboard's "Learning Progress" chart — a static placeholder in Milestone 1
— now plots **real average accuracy per gesture**, pulled from actual
practice attempts.

## 4. Database additions

New `gesture_attempts` table (see `backend/database/schema.sql`): one row
per practice attempt, storing the target/detected labels, all three
accuracy scores, whether it matched, and the feedback given — the raw data
behind both `/api/gesture/history` and `/api/gesture/stats`, and future
Milestone-3/4 features (progress forecasting, certification eligibility,
performance reports).

## 5. Frontend additions

New **Gesture Practice** page (`frontend/src/pages/GesturePractice.jsx`):
- Live webcam preview (`getUserMedia`) with a canvas overlay that draws the
  21 detected hand landmarks + skeleton connections in real time after each
  capture
- **Assess mode**: pick a target gesture, capture a frame, see the overall/
  hand-shape/position accuracy scores, a finger-by-finger correct/incorrect
  table, and corrective feedback
- **Free Detect mode**: capture a frame and see what gesture the engine
  recognizes, with no target comparison
- Recent attempts table + KPI cards (total attempts, avg/best accuracy,
  matched count) fed by `/api/gesture/history` and `/api/gesture/stats`

The Dashboard page was updated to show live gesture-practice KPIs and a real
per-gesture accuracy chart instead of the Milestone-1 zeroed-out placeholder.

## 6. Known limitations (by design, for this milestone)

- **5 gestures, not the full alphabet** — see the classifier rationale above.
- **Static frames only** — no motion/timing scoring yet (needs Milestone 3+
  continuous-capture work).
- **Webcam requires HTTPS or localhost** — browsers block `getUserMedia` on
  plain HTTP for any host other than `localhost`/`127.0.0.1`, so this works
  out of the box in local dev but needs TLS once deployed.
- **CPU-only inference** — MediaPipe Hands runs fine on CPU for single-frame
  snapshots; a production real-time video pipeline would benefit from the
  GPU-accelerated Tasks API once its model-download requirement is
  acceptable for the deployment environment.
