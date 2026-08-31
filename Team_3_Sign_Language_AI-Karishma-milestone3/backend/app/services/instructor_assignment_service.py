"""
CRUD for InstructorAssignment — an instructor pointing one learner at a
specific letter/motion-sign/word-sign to focus on next. Validates the
topic against each topic type's own real supported-list (the same
functions the practice endpoints and recommendation_service already
treat as the single source of truth for "what's practiceable"), so an
assignment can never reference a letter or sign the platform doesn't
actually support.
"""

import uuid
from datetime import datetime

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


class InvalidAssignment(ValueError):
    pass


def media_url(reference_media_path: str = None) -> str:
    """Turns the stored relative disk path into the /media/... URL the
    StaticFiles mount in main.py actually serves — the one place this
    translation happens, so create/list responses can never disagree."""
    return f"/media/{reference_media_path}" if reference_media_path else None


def create_assignment(
    db: Session,
    learner_id: str,
    instructor_id: str,
    topic: str,
    topic_type: str,
    reference_media_path: str = None,
    reference_media_type: str = None,
) -> InstructorAssignment:
    if topic_type not in TOPIC_TYPE_VALIDATORS:
        raise InvalidAssignment(f"Unknown topic_type: {topic_type}. Must be one of {list(TOPIC_TYPE_VALIDATORS)}.")

    supported = TOPIC_TYPE_VALIDATORS[topic_type]()
    if topic not in supported:
        raise InvalidAssignment(f"'{topic}' is not a supported {topic_type}.")

    learner = db.query(User).filter(User.id == learner_id, User.role == "learner").first()
    if learner is None:
        raise InvalidAssignment(f"No learner with id '{learner_id}'.")

    assignment = InstructorAssignment(
        id=str(uuid.uuid4()),
        learner_id=learner_id,
        instructor_id=instructor_id,
        topic=topic,
        topic_type=topic_type,
        reference_media_path=reference_media_path,
        reference_media_type=reference_media_type,
        created_at=datetime.utcnow(),
    )
    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return assignment


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

    return [
        {
            "id": row.id,
            "learner_id": row.learner_id,
            "instructor_id": row.instructor_id,
            "instructor_name": instructors.get(row.instructor_id),
            "topic": row.topic,
            "topic_type": row.topic_type,
            "reference_media_url": media_url(row.reference_media_path),
            "reference_media_type": row.reference_media_type,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def delete_assignment(db: Session, assignment_id: str) -> bool:
    row = db.query(InstructorAssignment).filter(InstructorAssignment.id == assignment_id).first()
    if row is None:
        return False
    delete_assignment_media(row.reference_media_path)
    db.delete(row)
    db.commit()
    return True
