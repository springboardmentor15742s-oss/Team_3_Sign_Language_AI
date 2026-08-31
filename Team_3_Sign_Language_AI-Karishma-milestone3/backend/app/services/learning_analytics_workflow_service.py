"""
Learning analytics workflow — Task 2 of the mentor-assigned work (August
2026). Collects and organizes a learner's activity + assessment data and
layers on top of the already-tested learning_analytics_service /
motion_sign_analytics_service outputs everything the brief asked the
workflow to produce: completion rate (by course), activity-frequency
patterns, commonly-missed and avoided topics, combined performance
metrics, and a current-vs-previous performance comparison — all in one
place, ready to feed both the dashboard (see routers/learner.py) and the
downloadable PDF report (see report_service.py).

No parallel source of truth: every number here is either read straight
from the existing per-letter/per-sign aggregates or computed directly
from PracticeAttempt / MotionSignAttempt timestamps — nothing here
re-derives accuracy differently than the services already covering it.
Follows the same null-vs-fabricated-number discipline used throughout
this codebase (learning_analytics_service, progress_service): a metric
without enough real data to support it is reported as unavailable with a
stated reason, never backfilled with an invented number.
"""

from collections import Counter
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from app.models.motion_sign_attempt import MotionSignAttempt
from app.models.practice_attempt import PracticeAttempt
from app.services.course_catalog_service import CATALOG
from app.services.learning_analytics_service import get_learner_analytics
from app.services.motion_sign_analytics_service import get_motion_sign_analytics

COMPARISON_WINDOW_DAYS = 7
MIN_SCORED_ATTEMPTS_FOR_COMPARISON = 3
TOP_N_MISSED = 5

_ATTEMPT_TRACKED_COURSE_IDS = {"alphabet-fundamentals", "everyday-gestures"}


def _completion_rate(analytics: dict, motion_analytics: dict) -> dict:
    """
    Coverage of the platform's built, attempt-tracked curriculum: what
    share of all letters + motion signs the learner has attempted at
    least once, both combined and broken out per built course. Courses
    with no attempt tracking (common-signs) or not yet built
    (conversational-fluency, workplace-communication) get
    completion_percent=None rather than an invented number — matching
    course_catalog_service's own tracks_progress/built flags.
    """
    per_letter = analytics["per_letter"]
    per_sign = motion_analytics["per_sign"]

    letters_attempted = sum(1 for s in per_letter.values() if s["attempts"] > 0)
    signs_attempted = sum(1 for s in per_sign.values() if s["attempts"] > 0)
    total_topics = len(per_letter) + len(per_sign)
    total_attempted = letters_attempted + signs_attempted

    by_course = [
        {
            "course_id": "alphabet-fundamentals",
            "title": "ASL Alphabet Fundamentals",
            "attempted_count": letters_attempted,
            "total_count": len(per_letter),
            "completion_percent": round(letters_attempted / len(per_letter) * 100, 1) if per_letter else None,
        },
        {
            "course_id": "everyday-gestures",
            "title": "Everyday Gestures",
            "attempted_count": signs_attempted,
            "total_count": len(per_sign),
            "completion_percent": round(signs_attempted / len(per_sign) * 100, 1) if per_sign else None,
        },
    ]
    for course in CATALOG:
        if course["id"] not in _ATTEMPT_TRACKED_COURSE_IDS:
            by_course.append({
                "course_id": course["id"],
                "title": course["title"],
                "attempted_count": None,
                "total_count": None,
                "completion_percent": None,
            })

    return {
        "overall_percent": round(total_attempted / total_topics * 100, 1) if total_topics else None,
        "attempted_count": total_attempted,
        "total_count": total_topics,
        "by_course": by_course,
    }


def _frequency_patterns(db: Session, learner_id: str) -> dict:
    """
    How often and how recently the learner actually practices, from real
    attempt timestamps — day granularity, consistent with
    learning_analytics_service's accuracy_trend and progress_service's
    streak logic (both already day-grained), not a fabricated
    "sessions" concept the data can't actually support.
    """
    letter_dates = [
        row.created_at.date() for row in
        db.query(PracticeAttempt.created_at).filter(PracticeAttempt.learner_id == learner_id).all()
        if row.created_at
    ]
    motion_dates = [
        row.created_at.date() for row in
        db.query(MotionSignAttempt.created_at).filter(MotionSignAttempt.learner_id == learner_id).all()
        if row.created_at
    ]
    all_dates = letter_dates + motion_dates
    if not all_dates:
        return {
            "days_active_total": 0,
            "days_active_last_7": 0,
            "days_active_last_30": 0,
            "avg_attempts_per_active_day": None,
            "last_active_date": None,
            "days_since_last_active": None,
            "most_active_weekday": None,
        }

    today = date.today()
    active_days = sorted(set(all_dates))
    days_active_last_7 = sum(1 for d in active_days if (today - d).days < 7)
    days_active_last_30 = sum(1 for d in active_days if (today - d).days < 30)
    last_active = max(active_days)

    weekday_counts = Counter(d.strftime("%A") for d in all_dates)
    most_active_weekday = weekday_counts.most_common(1)[0][0] if weekday_counts else None

    return {
        "days_active_total": len(active_days),
        "days_active_last_7": days_active_last_7,
        "days_active_last_30": days_active_last_30,
        "avg_attempts_per_active_day": round(len(all_dates) / len(active_days), 1),
        "last_active_date": last_active.isoformat(),
        "days_since_last_active": (today - last_active).days,
        "most_active_weekday": most_active_weekday,
    }


def _commonly_missed_and_avoided(analytics: dict, motion_analytics: dict) -> dict:
    """
    commonly_missed: topics ranked by raw incorrect-attempt COUNT (not
    percentage) — literally "which questions get missed most often",
    distinct from weak_areas' percentage-based, minimum-sample-gated
    definition used elsewhere in this codebase.
    avoided_topics: topics with zero attempts at all — the learner hasn't
    just struggled with these, they've never engaged with them, which is
    a different (and equally real) signal than a low score.
    """
    combined = [
        {"topic": letter, "topic_type": "letter", **stats} for letter, stats in analytics["per_letter"].items()
    ] + [
        {"topic": sign, "topic_type": "motion_sign", **stats} for sign, stats in motion_analytics["per_sign"].items()
    ]

    missed = sorted(
        (t for t in combined if t["incorrect"] > 0),
        key=lambda t: t["incorrect"], reverse=True,
    )[:TOP_N_MISSED]
    avoided = sorted(
        (t for t in combined if t["attempts"] == 0),
        key=lambda t: (t["topic_type"], t["topic"]),
    )

    return {
        "commonly_missed": [
            {
                "topic": t["topic"], "topic_type": t["topic_type"],
                "incorrect_count": t["incorrect"], "accuracy_percent": t["accuracy_percent"],
            }
            for t in missed
        ],
        "avoided_topics": [{"topic": t["topic"], "topic_type": t["topic_type"]} for t in avoided],
    }


def _period_accuracy(statuses: list[str]) -> dict:
    scored = [s for s in statuses if s in ("pass", "fail")]
    correct = sum(1 for s in scored if s == "pass")
    return {
        "attempts": len(statuses),
        "scored_attempts": len(scored),
        "accuracy_percent": round(correct / len(scored) * 100, 1) if scored else None,
    }


def _performance_comparison(db: Session, learner_id: str) -> dict:
    """
    Compares the learner's last COMPARISON_WINDOW_DAYS days of scored
    attempts against the COMPARISON_WINDOW_DAYS days before that —
    "current vs previous performance", as asked. Reports
    available=False with a stated reason when either window doesn't have
    enough scored attempts to compare honestly, rather than showing a
    delta computed from a couple of lucky/unlucky attempts.
    """
    # Explicit datetime boundaries (not bare `date` objects) so the
    # comparison against the DateTime created_at column is unambiguous
    # regardless of DB backend, rather than relying on a date/datetime
    # string-prefix comparison quirk to happen to work out.
    now = datetime.utcnow()
    current_start = now - timedelta(days=COMPARISON_WINDOW_DAYS)
    previous_start = now - timedelta(days=COMPARISON_WINDOW_DAYS * 2)

    def _statuses_since(model, since, until=None):
        q = db.query(model.status).filter(model.learner_id == learner_id, model.created_at >= since)
        if until is not None:
            q = q.filter(model.created_at < until)
        return [row[0] for row in q.all()]

    current_statuses = _statuses_since(PracticeAttempt, current_start) + _statuses_since(MotionSignAttempt, current_start)
    previous_statuses = (
        _statuses_since(PracticeAttempt, previous_start, current_start)
        + _statuses_since(MotionSignAttempt, previous_start, current_start)
    )

    current = _period_accuracy(current_statuses)
    previous = _period_accuracy(previous_statuses)

    if (
        current["scored_attempts"] < MIN_SCORED_ATTEMPTS_FOR_COMPARISON
        or previous["scored_attempts"] < MIN_SCORED_ATTEMPTS_FOR_COMPARISON
    ):
        return {
            "available": False,
            "reason": (
                f"Needs at least {MIN_SCORED_ATTEMPTS_FOR_COMPARISON} scored attempts in both the current and "
                f"previous {COMPARISON_WINDOW_DAYS}-day windows (have {current['scored_attempts']} and "
                f"{previous['scored_attempts']})."
            ),
            "current_period": current,
            "previous_period": previous,
            "accuracy_delta_percent": None,
            "trend": None,
        }

    delta = round(current["accuracy_percent"] - previous["accuracy_percent"], 1)
    trend = "improving" if delta > 2 else "declining" if delta < -2 else "steady"
    return {
        "available": True,
        "reason": None,
        "current_period": current,
        "previous_period": previous,
        "accuracy_delta_percent": delta,
        "trend": trend,
    }


def get_learning_analytics_workflow(db: Session, learner_id: str) -> dict:
    """
    Single entry point bundling every piece of Task 2's workflow. analytics
    / motion_analytics are recomputed fresh here (not cached) so the
    workflow always reflects the latest saved assessment, same as every
    other analytics/recommendation endpoint on this platform.
    """
    analytics = get_learner_analytics(db, learner_id)
    motion_analytics = get_motion_sign_analytics(db, learner_id)

    combined_scored = analytics["scored_attempts"] + motion_analytics["scored_attempts"]
    combined_correct = analytics["correct_count"] + motion_analytics["correct_count"]

    return {
        "learner_id": learner_id,
        "collected_data_summary": {
            "total_letter_attempts": analytics["total_attempts"],
            "total_motion_attempts": motion_analytics["total_attempts"],
            "total_scored_attempts": combined_scored,
        },
        "performance_metrics": {
            "overall_accuracy_percent": round(combined_correct / combined_scored * 100, 1) if combined_scored else None,
            "letter_accuracy_percent": analytics["overall_accuracy_percent"],
            "motion_sign_accuracy_percent": motion_analytics["overall_accuracy_percent"],
        },
        "completion_rate": _completion_rate(analytics, motion_analytics),
        "frequency_patterns": _frequency_patterns(db, learner_id),
        **_commonly_missed_and_avoided(analytics, motion_analytics),
        "performance_comparison": _performance_comparison(db, learner_id),
    }
