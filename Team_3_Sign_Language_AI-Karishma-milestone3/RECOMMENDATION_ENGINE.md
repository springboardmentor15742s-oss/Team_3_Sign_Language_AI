# Learning Recommendations Engine — Design Document

Task 3 of the mentor-assigned work (August 2026): a separate written
description of the recommendation workflow, distinct from the code
itself. The engine described here was built earlier in this project and
is production code today (`backend/app/services/recommendation_service.py`,
`backend/app/services/adaptive_learning_service.py`,
`backend/app/services/learning_plan_service.py`); this document explains
*why* it's built the way it is and how it satisfies each requirement in
the brief, not a re-implementation.

## Goal

Given a learner's real practice history, recommend what they should
practice next — personalized, weighted toward their weak areas, and
refreshed on every new assessment result. Recommendations can be
lessons, exercises, quizzes, or practice activities.

## Data sources — no separate source of truth

The engine reads directly from the same attempt tables every other part
of the platform reads from:

- `PracticeAttempt` — static ASL alphabet letters (26 letters).
- `MotionSignAttempt` — motion-based signs (Wave, Clap today).
- `LearningActivity` — logged active-practice time, used for the
  `activity_days` / `time_spent_minutes` context shown alongside a plan.

Nothing is pre-computed or cached into its own table. Every recommendation
request re-reads these tables and re-derives the plan from scratch. That's
a deliberate trade (a busy learner re-triggers the same aggregation
query on every dashboard load) made in favor of the explicit brief
requirement: recommendations must reflect the newest assessment results,
not stale historical data. There is no cache-invalidation bug to have,
because there is no cache.

## Two layers

The engine actually ships as two related outputs, because they answer
two different questions:

1. **`recommendation_service.get_recommendations()`** — "what should I
   practice next, in order?" A flat, ranked queue of individual topics
   (letters and/or motion signs), each with a one-line reason. This
   powers the dashboard's "Practice next" panel and the letter-only
   practice plan.

2. **`adaptive_learning_service.get_adaptive_learning_plan()`** — "what
   should my next study session actually look like?" A richer plan: a
   learning-level classification (beginner / intermediate / advanced), a
   trend per topic (improving / steady / declining / insufficient data),
   and for each of the top few priority topics, a small sequence of
   concrete activities (see "Activity types" below).

Both are recomputed from the same underlying data and agree with each
other — there is one weak/strong-area computation, not two competing
definitions of "weak."

## Personalization and skill-level tiering

`adaptive_learning_service._level()` classifies a learner into
`beginner` / `intermediate` / `advanced` from their combined overall
accuracy and total scored-attempt count (a learner with too few scored
attempts defaults to `beginner` rather than being classified from a
lucky or unlucky handful of tries). That level then selects which
activity sequence `_activities()` generates for a topic — a struggling
beginner gets a "review the basics, then a guided exercise, then an easy
quiz" sequence; a struggling advanced learner (someone whose accuracy
just dropped on a topic they'd previously mastered) gets a "revisit and
compare against similar signs" sequence instead. Same weak topic,
different activity plan, because the learner isn't at the same stage.

## Prioritizing weak areas over strong areas

This is the one requirement explicitly called out as a common failure
mode to avoid, so it's worth stating the exact mechanism, not just the
outcome.

`recommendation_service.get_recommendations()` builds its queue in a
fixed priority order and only fills a later tier once earlier tiers are
exhausted:

1. **Weak areas** — topics below 70% accuracy with at least 3 scored
   attempts, sorted worst-accuracy-first.
2. **Never-attempted topics** — so the queue still helps a learner build
   a complete skill set once weak areas are addressed.
3. **Rarely-attempted topics** — attempted, but not enough to judge yet.
4. **Mastered topics** — occasional spaced-repetition review, shown
   *last*, and only if there's still room in the queue.

A learner who is strong everywhere except one topic will always see that
one weak topic first, even though every other topic they own is a
"mastered" candidate — mastery review never crowds out a real gap. This
exact scenario (a learner strong at everything except one specific
topic) is one of the profiles covered in the test suite below, precisely
because it's the scenario most likely to expose a "recommends what
you're already good at" bug if the priority ordering were wrong.

`adaptive_learning_service.build_adaptive_plan_from_data()` applies the
same principle independently: `priority_topics = weak + needs_more_practice`,
falling back to `strong` topics only `if not priority_topics` — i.e. only
when there is truly nothing else left to recommend.

## Activity types

Every generated activity carries a `type` of `lesson`, `exercise`,
`quiz`, `practice`, `revision`, or `challenge` — the four categories
named in the brief (lessons, exercises, quizzes, practice activities)
plus two refinements (`revision` for spaced review, `challenge` for
mastery-level work) used at the top of the skill range where a learner
no longer needs a "lesson."

## Freshness

Neither engine persists a recommendation. `get_adaptive_learning_plan()`
and `get_recommendations()` are called fresh on every dashboard load and
after every saved assessment (see `backend/app/routers/learner.py`), so
the very next recommendation reflects the attempt a learner just
completed — there's no background job, no stale cache, and no separate
"recompute" step to remember to trigger.

## External resource links (e.g. YouTube)

Not built. Another team's recommendation engine reportedly links out to
external resources (YouTube was mentioned) as part of its suggestions.
This document deliberately does not add that here, because it's unclear
whether it's a hard requirement for this engine or an example of a
different team's approach — that's an open question for the mentor to
confirm. If it does become a requirement, the natural integration point
is `AdaptiveActivity` (`backend/app/schemas/adaptive_learning.py`): add
an optional `external_url` field, populate it only for topics where a
vetted resource actually exists (never a generic search-link fallback,
consistent with this project's no-fabrication conventions elsewhere),
and leave it `null` everywhere else.

## Testing across learner profiles

Required: test using different learner profiles and performance levels,
not just one person. `backend/scripts/test_recommendation_engine_profiles.py`
does this against a real (test) database, not mocks — it creates five
distinct profiles and asserts on the *shape* of the recommendation, not
just that a response comes back:

- **Brand-new learner, zero attempts** — every topic should surface as
  "not yet practiced," and the plan should default to `beginner`.
- **Strong learner** (letters and motion signs both high-accuracy) —
  should classify as `advanced` and list every topic under
  `completed_topics`.
- **Struggling learner** (letters and motion signs both low-accuracy) —
  should classify as `beginner`, and the top recommendation must be a
  genuine weak area, not a mastery-review filler.
- **Mixed learner** (strong at letters, weak at one specific motion
  sign) — the combined-topic-type queue must surface that one weak
  motion sign first, ahead of every strong letter. This is the specific
  scenario that would expose a "recommends what the user is already
  good at" bug if the priority logic above were implemented wrong.
- **The same mixed learner, filtered to `topic_type="letter"`** — checks
  that the letter-only view used by the static-alphabet Practice page
  never leaks a motion-sign recommendation it can't act on.

Run it from `backend/`:

```
venv/bin/python scripts/test_recommendation_engine_profiles.py
```

`backend/scripts/test_adaptive_learning.py` covers the same idea at the
pure-function level (`build_adaptive_plan_from_data`, no DB), across five
more accuracy bands (high / average / struggling / beginner / mixed
topic types), so the tiering logic is checked independently of database
setup too.
