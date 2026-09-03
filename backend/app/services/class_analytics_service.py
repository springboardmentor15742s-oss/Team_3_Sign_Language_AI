"""
Class-wide analytics: the one place that aggregates *across* an
instructor's roster rather than repeating single-learner math per row.
Before this existed, the roster page was just N independently-computed
per-learner numbers side by side — there was no way to see "how is my
class doing" without eyeballing every row. Deliberately reuses
learning_analytics_service.get_learner_analytics per learner (same
weak-area threshold, same accuracy semantics) rather than re-deriving
any of that math here, so this can never disagree with a learner's own
analytics or the roster's per-row numbers.
"""

from collections import defaultdict

from sqlalchemy.orm import Session

from app.models.instructor_assignment import InstructorAssignment
from app.models.instructor_learner import InstructorLearner
from app.models.user import User
from app.services.learning_analytics_service import get_learner_analytics

TOP_N_WEAK_LETTERS = 10


def get_roster_learner_ids(db: Session, instructor_id: str = None) -> list[str]:
    """Public (not module-private) since reporting_service also needs the
    exact same roster-vs-platform scoping — one place decides what "an
    instructor's roster" or "the whole platform" means, so a report can
    never disagree with the class overview panel about who's included."""
    if instructor_id is None:
        return [row.id for row in db.query(User.id).filter(User.role == "learner").all()]
    return [
        row.learner_id
        for row in db.query(InstructorLearner.learner_id)
        .filter(InstructorLearner.instructor_id == instructor_id)
        .all()
    ]


def get_class_analytics(db: Session, instructor_id: str = None) -> dict:
    learner_ids = get_roster_learner_ids(db, instructor_id)

    active_count = 0
    accuracies = []
    weak_letter_counts: dict[str, int] = defaultdict(int)

    for learner_id in learner_ids:
        analytics = get_learner_analytics(db, learner_id)
        if analytics["total_attempts"] > 0:
            active_count += 1
        if analytics["overall_accuracy_percent"] is not None:
            accuracies.append(analytics["overall_accuracy_percent"])
        for weak_area in analytics["weak_areas"]:
            weak_letter_counts[weak_area["letter"]] += 1

    average_accuracy = round(sum(accuracies) / len(accuracies), 1) if accuracies else None

    weak_letter_distribution = sorted(
        ({"letter": letter, "learner_count": count} for letter, count in weak_letter_counts.items()),
        key=lambda entry: (-entry["learner_count"], entry["letter"]),
    )[:TOP_N_WEAK_LETTERS]

    if learner_ids:
        assignment_rows = (
            db.query(InstructorAssignment.completed)
            .filter(InstructorAssignment.learner_id.in_(learner_ids))
            .all()
        )
    else:
        assignment_rows = []
    completed_count = sum(1 for (completed,) in assignment_rows if completed)
    outstanding_count = len(assignment_rows) - completed_count

    return {
        "learner_count": len(learner_ids),
        "active_learner_count": active_count,
        "average_accuracy_percent": average_accuracy,
        "weak_letter_distribution": weak_letter_distribution,
        "outstanding_assignment_count": outstanding_count,
        "completed_assignment_count": completed_count,
    }
