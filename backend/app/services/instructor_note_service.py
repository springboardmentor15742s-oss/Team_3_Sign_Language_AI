"""
Instructor-only notes on a learner's profile — see InstructorNote's
docstring for the visibility contract (staff-facing, never surfaced to
the learner's own routes).
"""

import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.instructor_note import InstructorNote
from app.models.user import User


def add_note(db: Session, instructor_id: str, learner_id: str, note: str) -> dict:
    row = InstructorNote(
        id=str(uuid.uuid4()),
        instructor_id=instructor_id,
        learner_id=learner_id,
        note=note,
        created_at=datetime.utcnow(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)

    author = db.query(User).filter(User.id == instructor_id).first()
    return _to_response_dict(row, author.name if author else None)


def list_notes_for_learner(db: Session, learner_id: str) -> list[dict]:
    rows = (
        db.query(InstructorNote)
        .filter(InstructorNote.learner_id == learner_id)
        .order_by(InstructorNote.created_at.desc())
        .all()
    )
    instructor_ids = {row.instructor_id for row in rows}
    instructors = {
        u.id: u.name for u in db.query(User).filter(User.id.in_(instructor_ids)).all()
    } if instructor_ids else {}

    return [_to_response_dict(row, instructors.get(row.instructor_id)) for row in rows]


def _to_response_dict(row: InstructorNote, instructor_name: str = None) -> dict:
    return {
        "id": row.id,
        "learner_id": row.learner_id,
        "instructor_id": row.instructor_id,
        "instructor_name": instructor_name,
        "note": row.note,
        "created_at": row.created_at,
    }
