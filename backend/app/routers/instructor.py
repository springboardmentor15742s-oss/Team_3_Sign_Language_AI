from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.instructor import LearnerRosterResponse
from app.schemas.instructor_assignment import AssignmentListResponse, AssignmentResponse
from app.services.auth_dependency import require_role
from app.services.instructor_service import get_learner_roster
from app.services.media_upload_service import UnsupportedMedia, save_assignment_media
from app.services.instructor_assignment_service import (
    InvalidAssignment,
    create_assignment,
    delete_assignment,
    list_assignments_for_learner,
    media_url,
)

router = APIRouter(prefix="/api/instructor", tags=["Instructor"])

@router.get("/learners", response_model=LearnerRosterResponse)
def list_learners(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    return {"learners": get_learner_roster(db)}


@router.post("/learners/{learner_id}/assignments", response_model=AssignmentResponse)
async def create_learner_assignment(
    learner_id: str,
    topic: str = Form(...),
    topic_type: str = Form(...),
    reference_media: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    """Point a learner at a specific letter/motion-sign/word-sign to focus on next,
    optionally with a reference photo/video showing the correct sign. Topic is
    validated against that topic type's own real supported list, so an assignment
    can never reference something the platform doesn't actually support; the
    attached file (if any) is validated by media_upload_service before it ever
    touches disk. Multipart form rather than JSON specifically to carry that file."""
    reference_media_path = None
    reference_media_type = None
    if reference_media is not None and reference_media.filename:
        data = await reference_media.read()
        try:
            reference_media_path, reference_media_type = save_assignment_media(reference_media, data)
        except UnsupportedMedia as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    try:
        assignment = create_assignment(
            db, learner_id=learner_id, instructor_id=current_user.id,
            topic=topic, topic_type=topic_type,
            reference_media_path=reference_media_path, reference_media_type=reference_media_type,
        )
    except InvalidAssignment as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return AssignmentResponse(
        id=assignment.id,
        learner_id=assignment.learner_id,
        instructor_id=assignment.instructor_id,
        instructor_name=current_user.name,
        topic=assignment.topic,
        topic_type=assignment.topic_type,
        reference_media_url=media_url(assignment.reference_media_path),
        reference_media_type=assignment.reference_media_type,
        created_at=assignment.created_at,
    )


@router.get("/learners/{learner_id}/assignments", response_model=AssignmentListResponse)
def list_learner_assignments(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    return {"assignments": list_assignments_for_learner(db, learner_id)}


@router.delete("/assignments/{assignment_id}")
def delete_learner_assignment(
    assignment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    deleted = delete_assignment(db, assignment_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    return {"deleted": True}
