"""
The one gap the existing per-learner-focused analytics (learning_analytics_
service, learning_analytics_workflow_service, progress_service) and the
existing roster-wide snapshots (class_analytics_service, admin_service)
both leave open: neither shows a class/platform how it's trending over
time, or how its learners are distributed across course completion —
both only ever answer "how are things right now."

accuracy_trend here reuses get_learner_analytics's own day-by-day
accuracy_trend (PracticeAttempt/alphabet-scoped) rather than inventing a
combined-across-topic-types definition of "accuracy" — class_analytics_
service's average_accuracy_percent and admin_service's overall
accuracy_percent are both already alphabet-only for the same reason (see
learning_analytics_service's own docstring: this platform's "accuracy"
has one settled meaning throughout the app), so this trend can never
disagree with the snapshot numbers already shown alongside it on
ClassOverviewPanel.

Course completion reuses course_catalog_service's own progress_percent
per learner (no second progress calculation) and, for the three
certifiable courses, cross-references the real Certificate table so
"completed" here can never disagree with what actually earned a
certificate.
"""

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.models.user import User
from app.services.class_analytics_service import get_roster_learner_ids
from app.services.course_catalog_service import CATALOG, get_course_catalog
from app.services.learning_analytics_service import get_learner_analytics

TREND_DAYS_LIMIT = 30


def get_roster_accuracy_trend(db: Session, instructor_id: str = None) -> list[dict]:
    """
    Day-by-day accuracy across every learner in scope, aggregated by
    summing each day's real correct/scored_attempts counts across
    learners first and dividing once at the end — not by averaging
    each learner's daily percentage, which would let a learner with 1
    attempt count as much as one with 50 and distort the true rate.
    Only days with at least one scored attempt from someone in scope
    appear, same "real data or nothing" rule as everywhere else.
    """
    learner_ids = get_roster_learner_ids(db, instructor_id)
    by_day_correct: dict[str, int] = defaultdict(int)
    by_day_scored: dict[str, int] = defaultdict(int)
    by_day_attempts: dict[str, int] = defaultdict(int)

    for learner_id in learner_ids:
        analytics = get_learner_analytics(db, learner_id)
        for point in analytics["accuracy_trend"]:
            day = point["date"]
            if day == "unknown":
                continue
            by_day_attempts[day] += point["attempts"]
            by_day_scored[day] += point["scored_attempts"]
            by_day_correct[day] += point["correct"]

    trend = []
    for day in sorted(by_day_attempts)[-TREND_DAYS_LIMIT:]:
        scored = by_day_scored[day]
        trend.append({
            "date": day,
            "attempts": by_day_attempts[day],
            "scored_attempts": scored,
            "accuracy_percent": round((by_day_correct[day] / scored) * 100, 1) if scored else None,
        })
    return trend


_CERTIFIABLE_COURSE_IDS = {"alphabet-fundamentals", "everyday-gestures", "conversational-fluency"}


def get_roster_course_completion(db: Session, instructor_id: str = None) -> list[dict]:
    """
    Per course, how the roster/platform splits across not-started /
    in-progress / completed (progress_percent buckets from
    course_catalog_service), plus a real certified_count for the three
    certifiable courses — completed and certified are reported
    separately on purpose: reaching 100% progress makes a learner
    ELIGIBLE, it doesn't retroactively certify them (auto-issuance still
    has to actually run — see certificate_service — and a manually
    issued certificate can exist without 100% progress at all), so the
    two numbers are real and allowed to differ.
    """
    learner_ids = get_roster_learner_ids(db, instructor_id)

    certified_counts: dict[str, int] = defaultdict(int)
    if learner_ids:
        cert_rows = (
            db.query(Certificate.course_id)
            .filter(Certificate.learner_id.in_(learner_ids), Certificate.revoked.is_(False))
            .all()
        )
        for (course_id,) in cert_rows:
            certified_counts[course_id] += 1

    course_meta = {c["id"]: c for c in CATALOG if c["tracks_progress"] and c["built"]}
    not_started = {course_id: 0 for course_id in course_meta}
    in_progress = {course_id: 0 for course_id in course_meta}
    completed = {course_id: 0 for course_id in course_meta}

    for learner_id in learner_ids:
        analytics = get_learner_analytics(db, learner_id)
        for course in get_course_catalog(analytics, db, learner_id):
            if course["id"] not in course_meta:
                continue
            percent = course["progress_percent"]
            if percent is None or percent == 0:
                not_started[course["id"]] += 1
            elif percent >= 100:
                completed[course["id"]] += 1
            else:
                in_progress[course["id"]] += 1

    return [
        {
            "course_id": course_id,
            "course_title": meta["title"],
            "learner_count": len(learner_ids),
            "not_started_count": not_started[course_id],
            "in_progress_count": in_progress[course_id],
            "completed_count": completed[course_id],
            "certified_count": certified_counts.get(course_id, 0) if course_id in _CERTIFIABLE_COURSE_IDS else None,
        }
        for course_id, meta in course_meta.items()
    ]


def get_class_trends(db: Session, instructor_id: str = None) -> dict:
    return {
        "accuracy_trend": get_roster_accuracy_trend(db, instructor_id),
        "course_completion": get_roster_course_completion(db, instructor_id),
    }
