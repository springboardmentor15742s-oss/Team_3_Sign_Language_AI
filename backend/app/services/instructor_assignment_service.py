"""
CRUD for InstructorAssignment — an instructor pointing one (or several)
learners at a specific letter/motion-sign/word-sign to focus on next.
Validates the topic against each topic type's own real supported-list
(the same functions the practice endpoints and recommendation_service
already treat as the single source of truth for "what's practiceable"),
so an assignment can never reference a letter or sign the platform
doesn't actually support.
"""

import uuid
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.models.instructor_assignment import InstructorAssignment
from app.models.user import User
from app.services.gesture_recognition_service import get_supported_letters
from app.services.media_upload_service import delete_assignment_media
from app.services.motion_sign_service import SUPPORTED_MOTION_SIGNS
from app.services.word_sign_service import get_supported_word_signs

TOPIC_TYPE_VALIDATORS = {
    "letter": get_supported_letters,
    "motion_sign": lambda: SUPPORTED_MOTION_SIGNS,
    "word_sign": get_supported_word_signs,
}

# notes/due_date arrive as multipart Form(...) fields (see instructor.py's
# create-assignment endpoints), not a pydantic JSON body, so nothing
# upstream bounds their length the way a Field(max_length=...) would for a
# normal request body — this is the actual enforcement point.
MAX_NOTES_LENGTH = 2000


class InvalidAssignment(ValueError):
    pass


def media_url(reference_media_path: str = None) -> str:
    """Turns the stored relative disk path into the /media/... URL the
    StaticFiles mount in main.py actually serves — the one place this
    translation happens, so create/list responses can never disagree."""
    return f"/media/{reference_media_path}" if reference_media_path else None


def _validate_topic(topic: str, topic_type: str) -> None:
    if topic_type not in TOPIC_TYPE_VALIDATORS:
        raise InvalidAssignment(f"Unknown topic_type: {topic_type}. Must be one of {list(TOPIC_TYPE_VALIDATORS)}.")

    supported = TOPIC_TYPE_VALIDATORS[topic_type]()
    if topic not in supported:
        raise InvalidAssignment(f"'{topic}' is not a supported {topic_type}.")


def _validate_due_date(due_date: str = None) -> None:
    if due_date is None or due_date == "":
        return
    try:
        date.fromisoformat(due_date)
    except ValueError:
        raise InvalidAssignment(f"due_date must be an ISO date (YYYY-MM-DD), got '{due_date}'.")


def _validate_notes(notes: str = None) -> None:
    if notes is not None and len(notes) > MAX_NOTES_LENGTH:
        raise InvalidAssignment(f"notes must be at most {MAX_NOTES_LENGTH} characters (got {len(notes)}).")


def _to_response_dict(row: InstructorAssignment, instructor_name: str = None) -> dict:
    return {
        "id": row.id,
        "learner_id": row.learner_id,
        "instructor_id": row.instructor_id,
        "instructor_name": instructor_name,
        "topic": row.topic,
        "topic_type": row.topic_type,
        "notes": row.notes,
        "due_date": row.due_date,
        "completed": bool(row.completed),
        "completed_at": row.completed_at,
        "reference_media_url": media_url(row.reference_media_path),
        "reference_media_type": row.reference_media_type,
        "created_at": row.created_at,
    }


def create_assignment(
    db: Session,
    learner_id: str,
    instructor_id: str,
    topic: str,
    topic_type: str,
    notes: str = None,
    due_date: str = None,
    reference_media_path: str = None,
    reference_media_type: str = None,
) -> InstructorAssignment:
    _validate_topic(topic, topic_type)
    _validate_due_date(due_date)
    _validate_notes(notes)

    learner = db.query(User).filter(User.id == learner_id, User.role == "learner").first()
    if learner is None:
        raise InvalidAssignment(f"No learner with id '{learner_id}'.")

    assignment = InstructorAssignment(
        id=str(uuid.uuid4()),
        learner_id=learner_id,
        instructor_id=instructor_id,
        topic=topic,
        topic_type=topic_type,
        notes=notes or None,
        due_date=due_date or None,
        completed=False,
        completed_at=None,
        reference_media_path=reference_media_path,
        reference_media_type=reference_media_type,
        created_at=datetime.utcnow(),
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


def create_assignments_for_many(
    db: Session,
    learner_ids: list[str],
    instructor_id: str,
    topic: str,
    topic_type: str,
    notes: str = None,
    due_date: str = None,
    reference_media_path: str = None,
    reference_media_type: str = None,
) -> list[InstructorAssignment]:
    """Bulk-assign the same topic (and the same attached reference media,
    if any — one upload, reused across every row rather than re-uploaded
    per learner) to several learners at once. Validates everything up
    front so a bad topic_type or one missing learner_id fails the whole
    batch rather than leaving a half-created set of assignments behind."""
    if not learner_ids:
        raise InvalidAssignment("Select at least one learner to assign to.")

    _validate_topic(topic, topic_type)
    _validate_due_date(due_date)
    _validate_notes(notes)

    unique_ids = list(dict.fromkeys(learner_ids))  # de-dupe, preserve order
    found = db.query(User).filter(User.id.in_(unique_ids), User.role == "learner").all()
    found_ids = {u.id for u in found}
    missing = [lid for lid in unique_ids if lid not in found_ids]
    if missing:
        raise InvalidAssignment(f"No learner with id(s): {', '.join(missing)}.")

    created = []
    for learner_id in unique_ids:
        assignment = InstructorAssignment(
            id=str(uuid.uuid4()),
            learner_id=learner_id,
            instructor_id=instructor_id,
            topic=topic,
            topic_type=topic_type,
            notes=notes or None,
            due_date=due_date or None,
            completed=False,
            completed_at=None,
            reference_media_path=reference_media_path,
            reference_media_type=reference_media_type,
            created_at=datetime.utcnow(),
        )
        db.add(assignment)
        created.append(assignment)

    db.commit()
    for assignment in created:
        db.refresh(assignment)
    return created


def get_assignment(db: Session, assignment_id: str) -> InstructorAssignment:
    return db.query(InstructorAssignment).filter(InstructorAssignment.id == assignment_id).first()


def list_assignments_for_learner(db: Session, learner_id: str) -> list[dict]:
    """Newest first, with the assigning instructor's name attached (a
    small join, not a second source of truth — instructor_name is purely
    display data resolved from the same User row every login page reads)."""
    rows = (
        db.query(InstructorAssignment)
        .filter(InstructorAssignment.learner_id == learner_id)
        .order_by(InstructorAssignment.created_at.desc())
        .all()
    )
    instructor_ids = {row.instructor_id for row in rows}
    instructors = {
        u.id: u.name for u in db.query(User).filter(User.id.in_(instructor_ids)).all()
    } if instructor_ids else {}

    return [_to_response_dict(row, instructors.get(row.instructor_id)) for row in rows]


def delete_assignment(db: Session, assignment_id: str) -> bool:
    row = db.query(InstructorAssignment).filter(InstructorAssignment.id == assignment_id).first()
    if row is None:
        return False
    delete_assignment_media(row.reference_media_path)
    db.delete(row)
    db.commit()
    return True


def set_assignment_completed(db: Session, assignment_id: str, learner_id: str, completed: bool) -> dict:
    """Learner-driven completion toggle — scoped to assignment_id AND
    learner_id together so a learner can only ever mark their own
    assignments, never someone else's by guessing an id. Returns None
    (via the caller's 404) when no matching row exists."""
    row = (
        db.query(InstructorAssignment)
        .filter(InstructorAssignment.id == assignment_id, InstructorAssignment.learner_id == learner_id)
        .first()
    )
    if row is None:
        return None

    row.completed = completed
    row.completed_at = datetime.utcnow() if completed else None
    db.commit()
    db.refresh(row)

    instructor = db.query(User).filter(User.id == row.instructor_id).first()
    return _to_response_dict(row, instructor.name if instructor else None)
