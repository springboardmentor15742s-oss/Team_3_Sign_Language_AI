import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.instructor_learner import InstructorLearner
from app.models.user import User
from app.services.gesture_recognition_service import get_supported_letters
from app.services.learning_analytics_service import get_learner_analytics


class RosterError(ValueError):
    pass


def _build_roster_entry(db: Session, learner: User, total_letters: int) -> dict:
    analytics = get_learner_analytics(db, learner.id)
    letters_scored = sum(
        1 for stats in analytics["per_letter"].values() if stats["accuracy_percent"] is not None
    )
    return {
        "learner_id": learner.id,
        "name": learner.name,
        "email": learner.email,
        "total_attempts": analytics["total_attempts"],
        "overall_accuracy_percent": analytics["overall_accuracy_percent"],
        "letters_scored": letters_scored,
        "total_letters": total_letters,
        "weak_area_count": len(analytics["weak_areas"]),
    }


def get_learner_roster(db: Session, instructor_id: str = None) -> list[dict]:
    """
    Builds a read-only roster for instructors, with lifetime stats.
    Reuses learning_analytics_service for every learner rather than
    re-deriving accuracy/weak-area math here, so the weak-area threshold
    stays defined in exactly one place.

    instructor_id=None returns every learner in the system — this is
    the admin path, since an admin isn't "a" class's instructor and
    ownership doesn't apply to them. Passing a real instructor_id scopes
    the roster to only the learners that instructor has added via
    add_learner_to_roster (see InstructorLearner) — the ownership model
    that replaced the earlier any-instructor-sees-any-learner behavior.

    A learner with zero attempts still appears, with
    overall_accuracy_percent=None (never 0) — get_learner_analytics
    already preserves that distinction.
    """
    total_letters = len(get_supported_letters())

    if instructor_id is None:
        learners = db.query(User).filter(User.role == "learner").all()
    else:
        learner_ids = [
            row.learner_id
            for row in db.query(InstructorLearner.learner_id)
            .filter(InstructorLearner.instructor_id == instructor_id)
            .all()
        ]
        learners = (
            db.query(User).filter(User.id.in_(learner_ids), User.role == "learner").all()
            if learner_ids
            else []
        )

    return [_build_roster_entry(db, learner, total_letters) for learner in learners]


def add_learner_to_roster(db: Session, instructor_id: str, learner_email: str) -> dict:
    learner = db.query(User).filter(User.email == learner_email, User.role == "learner").first()
    if learner is None:
        raise RosterError(f"No learner found with email '{learner_email}'.")
    return _add_learner(db, instructor_id, learner)


def add_learner_to_roster_by_id(db: Session, instructor_id: str, learner_id: str) -> dict:
    """Same as add_learner_to_roster, but by id rather than email — for
    InstructorLearnerDetail.tsx, which already knows a real learner_id
    (from the URL, resolved via require_self_or_staff-gated data) but
    not necessarily that learner's email when they're not yet on the
    roster (that's exactly the rosterNotFound case it's used from)."""
    learner = db.query(User).filter(User.id == learner_id, User.role == "learner").first()
    if learner is None:
        raise RosterError(f"No learner with id '{learner_id}'.")
    return _add_learner(db, instructor_id, learner)


def _add_learner(db: Session, instructor_id: str, learner: User) -> dict:
    existing = (
        db.query(InstructorLearner)
        .filter(InstructorLearner.instructor_id == instructor_id, InstructorLearner.learner_id == learner.id)
        .first()
    )
    if existing is None:
        db.add(InstructorLearner(
            id=str(uuid.uuid4()),
            instructor_id=instructor_id,
            learner_id=learner.id,
            created_at=datetime.utcnow(),
        ))
        db.commit()

    total_letters = len(get_supported_letters())
    return _build_roster_entry(db, learner, total_letters)


def remove_learner_from_roster(db: Session, instructor_id: str, learner_id: str) -> bool:
    row = (
        db.query(InstructorLearner)
        .filter(InstructorLearner.instructor_id == instructor_id, InstructorLearner.learner_id == learner_id)
        .first()
    )
    if row is None:
        return False
    db.delete(row)
    db.commit()
    return True


def is_learner_in_roster(db: Session, instructor_id: str, learner_id: str) -> bool:
    return (
        db.query(InstructorLearner)
        .filter(InstructorLearner.instructor_id == instructor_id, InstructorLearner.learner_id == learner_id)
        .first()
        is not None
    )
