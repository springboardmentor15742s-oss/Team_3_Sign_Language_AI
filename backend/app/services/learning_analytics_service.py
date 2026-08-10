from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.practice_attempt import PracticeAttempt
from app.services.assessment_report_service import generate_session_report

WEAK_AREA_ACCURACY_THRESHOLD = 70.0
WEAK_AREA_MIN_SCORED_ATTEMPTS = 3  # avoid flagging a letter on a single unlucky miss
TOP_N_LETTERS = 5


def _attempt_to_result(attempt: PracticeAttempt) -> dict:
    """Reshapes a PracticeAttempt row back into a sign_assessment_service-shaped dict."""
    return {
        "status": attempt.status,
        "correct": attempt.correct,
        "confidence": attempt.confidence,
        "target_letter": attempt.target_letter,
        "predicted_letter": attempt.predicted_letter,
    }


def get_learner_analytics(db: Session, learner_id: str) -> dict:
    """
    Aggregates a learner's full PracticeAttempt history into an overall
    summary, a day-by-day accuracy trend, and per-letter breakdowns —
    including which letters are practiced most/least and which are
    "weak areas" (accuracy below WEAK_AREA_ACCURACY_THRESHOLD with at
    least WEAK_AREA_MIN_SCORED_ATTEMPTS scored attempts).

    Reuses assessment_report_service.generate_session_report for the
    overall and per-letter aggregation (same accuracy semantics: computed
    over scored attempts only, excluding no_attempt_detected) so a
    learner's lifetime stats are computed identically to a single
    session's stats.
    """
    attempts = (
        db.query(PracticeAttempt)
        .filter(PracticeAttempt.learner_id == learner_id)
        .order_by(PracticeAttempt.created_at.asc())
        .all()
    )

    results = [_attempt_to_result(a) for a in attempts]
    overall = generate_session_report(results)

    by_day: dict[str, list[dict]] = defaultdict(list)
    for attempt, result in zip(attempts, results):
        day = attempt.created_at.date().isoformat() if attempt.created_at else "unknown"
        by_day[day].append(result)

    accuracy_trend = []
    for day in sorted(by_day):
        day_report = generate_session_report(by_day[day])
        accuracy_trend.append({
            "date": day,
            "attempts": day_report["total_attempts"],
            "scored_attempts": day_report["scored_attempts"],
            "correct": day_report["correct_count"],
            "accuracy_percent": day_report["overall_accuracy_percent"],
        })

    per_letter = overall["per_letter"]

    letters_by_practice_count = sorted(
        per_letter.items(), key=lambda item: item[1]["attempts"], reverse=True
    )
    most_practiced_letters = [
        {"letter": letter, "attempts": stats["attempts"]}
        for letter, stats in letters_by_practice_count[:TOP_N_LETTERS]
    ]
    least_practiced_letters = [
        {"letter": letter, "attempts": stats["attempts"]}
        for letter, stats in letters_by_practice_count[-TOP_N_LETTERS:][::-1]
    ]

    weak_areas = [
        {
            "letter": letter,
            "accuracy_percent": stats["accuracy_percent"],
            "scored_attempts": stats["correct"] + stats["incorrect"],
        }
        for letter, stats in per_letter.items()
        if stats["accuracy_percent"] is not None
        and stats["accuracy_percent"] < WEAK_AREA_ACCURACY_THRESHOLD
        and (stats["correct"] + stats["incorrect"]) >= WEAK_AREA_MIN_SCORED_ATTEMPTS
    ]
    weak_areas.sort(key=lambda w: w["accuracy_percent"])

    return {
        "learner_id": learner_id,
        "total_attempts": overall["total_attempts"],
        "correct_count": overall["correct_count"],
        "incorrect_count": overall["incorrect_count"],
        "no_attempt_count": overall["no_attempt_count"],
        "scored_attempts": overall["scored_attempts"],
        "overall_accuracy_percent": overall["overall_accuracy_percent"],
        "accuracy_trend": accuracy_trend,
        "per_letter": per_letter,
        "most_practiced_letters": most_practiced_letters,
        "least_practiced_letters": least_practiced_letters,
        "weak_areas": weak_areas,
    }
