import re
from io import BytesIO
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.instructor import (
    AddLearnerRequest,
    ClassAnalyticsResponse,
    LearnerRosterResponse,
)
from app.schemas.instructor_assignment import AssignmentListResponse, AssignmentResponse
from app.schemas.instructor_note import NoteCreate, NoteListResponse, NoteResponse
from app.schemas.certificate import CertificateResponse, IssueCertificateRequest, RevokeCertificateRequest
from app.schemas.class_trends import ClassTrendsResponse
from app.schemas.reporting import AssignmentReportResponse, ClassReportResponse
from app.services.auth_dependency import require_role
from app.services.certificate_service import (
    CertificateError,
    get_certificate,
    issue_certificate_manually,
    revoke_certificate,
)
from app.services.class_trends_service import get_class_trends
from app.services.class_analytics_service import get_class_analytics
from app.services.instructor_note_service import add_note, list_notes_for_learner
from app.services.instructor_service import (
    RosterError,
    add_learner_to_roster,
    add_learner_to_roster_by_id,
    get_learner_roster,
    is_learner_in_roster,
    remove_learner_from_roster,
)
from app.services.media_upload_service import UnsupportedMedia, save_assignment_media
from app.services.instructor_assignment_service import (
    InvalidAssignment,
    create_assignment,
    create_assignments_for_many,
    delete_assignment,
    get_assignment,
    list_assignments_for_learner,
    media_url,
)
from app.services.reporting_pdf_service import render_assignment_report_pdf, render_class_report_pdf
from app.services.reporting_service import assemble_assignment_report, assemble_class_report

router = APIRouter(prefix="/api/instructor", tags=["Instructor"])


def _slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "report"


def _roster_scope(current_user: User) -> Optional[str]:
    """Admins see/manage every learner (they're not "a" class's
    instructor); the instructor role is scoped to their own roster. One
    helper so every endpoint below applies the exemption identically."""
    return None if current_user.role == "admin" else current_user.id


def _require_own_learner(db: Session, current_user: User, learner_id: str) -> None:
    """Blocks an instructor from creating assignments/notes for a
    learner outside their roster. Admins are exempt (see _roster_scope)."""
    if current_user.role == "admin":
        return
    if not is_learner_in_roster(db, current_user.id, learner_id):
        raise HTTPException(
            status_code=400,
            detail="That learner isn't on your roster. Add them first.",
        )


def _assignment_response(assignment, instructor_name: str) -> AssignmentResponse:
    return AssignmentResponse(
        id=assignment.id,
        learner_id=assignment.learner_id,
        instructor_id=assignment.instructor_id,
        instructor_name=instructor_name,
        topic=assignment.topic,
        topic_type=assignment.topic_type,
        notes=assignment.notes,
        due_date=assignment.due_date,
        completed=bool(assignment.completed),
        completed_at=assignment.completed_at,
        reference_media_url=media_url(assignment.reference_media_path),
        reference_media_type=assignment.reference_media_type,
        created_at=assignment.created_at,
    )


@router.get("/learners", response_model=LearnerRosterResponse)
def list_learners(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    return {"learners": get_learner_roster(db, instructor_id=_roster_scope(current_user))}


@router.post("/learners", response_model=LearnerRosterResponse)
def add_learner(
    payload: AddLearnerRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    """Adds a learner (by email) to the instructor's own roster. Admins
    can call this too, but since admins already see every learner
    regardless of roster membership, it has no visible effect for them."""
    try:
        add_learner_to_roster(db, instructor_id=current_user.id, learner_email=payload.learner_email)
    except RosterError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"learners": get_learner_roster(db, instructor_id=_roster_scope(current_user))}


@router.post("/learners/{learner_id}/roster", response_model=LearnerRosterResponse)
def add_learner_by_id(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    """Same as POST /learners (add by email), but by id — used by
    InstructorLearnerDetail.tsx's "add to my roster" prompt, which
    already has a valid learner_id from the URL but not necessarily
    that learner's email."""
    try:
        add_learner_to_roster_by_id(db, instructor_id=current_user.id, learner_id=learner_id)
    except RosterError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"learners": get_learner_roster(db, instructor_id=_roster_scope(current_user))}


@router.delete("/learners/{learner_id}")
def remove_learner(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    removed = remove_learner_from_roster(db, instructor_id=current_user.id, learner_id=learner_id)
    if not removed:
        raise HTTPException(status_code=404, detail="That learner isn't on your roster.")
    return {"removed": True}


@router.get("/class-analytics", response_model=ClassAnalyticsResponse)
def class_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    return get_class_analytics(db, instructor_id=_roster_scope(current_user))


@router.get("/class-trends", response_model=ClassTrendsResponse)
def class_trends(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    """Roster/platform accuracy over time plus a course-completion
    breakdown — the trend-over-time view class-analytics' snapshot
    numbers don't cover. Same _roster_scope as every other endpoint
    here, so an admin automatically gets the platform-wide version."""
    return get_class_trends(db, instructor_id=_roster_scope(current_user))


@router.get("/reports/class/pdf")
def get_class_report_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    """PDF export of the same class-analytics numbers shown on the roster
    page, plus a printable per-learner roster listing. Scope (own roster
    vs. whole platform) comes from _roster_scope, same as /class-analytics —
    an admin calling this gets a platform-wide report automatically."""
    report_data = assemble_class_report(db, instructor_id=_roster_scope(current_user))
    report = ClassReportResponse(**report_data)
    pdf_bytes = render_class_report_pdf(report, current_user.name)

    filename = f"{report.scope}-report-{report.generated_at.date().isoformat()}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/reports/assignments", response_model=AssignmentReportResponse)
def get_assignment_report(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    """In-app view of the assignment/completion report — same scoping
    as every other roster-aware endpoint above."""
    return assemble_assignment_report(db, instructor_id=_roster_scope(current_user))


@router.get("/reports/assignments/pdf")
def get_assignment_report_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    report_data = assemble_assignment_report(db, instructor_id=_roster_scope(current_user))
    report = AssignmentReportResponse(**report_data)
    pdf_bytes = render_assignment_report_pdf(report, current_user.name)

    filename = f"{report.scope}-assignment-report-{report.generated_at.date().isoformat()}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/learners/{learner_id}/assignments", response_model=AssignmentResponse)
async def create_learner_assignment(
    learner_id: str,
    topic: str = Form(...),
    topic_type: str = Form(...),
    notes: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    reference_media: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    """Point a learner at a specific letter/motion-sign/word-sign to focus on next,
    optionally with instructions, a due date, and a reference photo/video showing
    the correct sign. Topic is validated against that topic type's own real
    supported list, so an assignment can never reference something the platform
    doesn't actually support; the attached file (if any) is validated by
    media_upload_service before it ever touches disk. Multipart form rather than
    JSON specifically to carry that file."""
    _require_own_learner(db, current_user, learner_id)

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
            topic=topic, topic_type=topic_type, notes=notes, due_date=due_date,
            reference_media_path=reference_media_path, reference_media_type=reference_media_type,
        )
    except InvalidAssignment as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return _assignment_response(assignment, current_user.name)


@router.post("/assignments", response_model=AssignmentListResponse)
async def create_assignments_bulk(
    learner_ids: List[str] = Form(...),
    topic: str = Form(...),
    topic_type: str = Form(...),
    notes: Optional[str] = Form(None),
    due_date: Optional[str] = Form(None),
    reference_media: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    """Same as create_learner_assignment, but for several learners at
    once — one topic (and one uploaded reference file, reused across
    every row) fanned out into one InstructorAssignment per selected
    learner. Every target learner must already be on the instructor's
    roster (same ownership rule as the single-learner endpoint)."""
    for learner_id in learner_ids:
        _require_own_learner(db, current_user, learner_id)

    reference_media_path = None
    reference_media_type = None
    if reference_media is not None and reference_media.filename:
        data = await reference_media.read()
        try:
            reference_media_path, reference_media_type = save_assignment_media(reference_media, data)
        except UnsupportedMedia as exc:
            raise HTTPException(status_code=400, detail=str(exc))

    try:
        assignments = create_assignments_for_many(
            db, learner_ids=learner_ids, instructor_id=current_user.id,
            topic=topic, topic_type=topic_type, notes=notes, due_date=due_date,
            reference_media_path=reference_media_path, reference_media_type=reference_media_type,
        )
    except InvalidAssignment as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return {"assignments": [_assignment_response(a, current_user.name) for a in assignments]}


@router.get("/learners/{learner_id}/assignments", response_model=AssignmentListResponse)
def list_learner_assignments(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    # Deliberately not roster-gated, unlike the write endpoints below:
    # InstructorLearnerDetail.tsx already handles "this learner isn't on
    # your roster" as a soft warning (rosterNotFound) while still showing
    # the learner's real data on a direct link — mirroring that here
    # instead of hard-failing the whole page load keeps that UX intact.
    return {"assignments": list_assignments_for_learner(db, learner_id)}


@router.delete("/assignments/{assignment_id}")
def delete_learner_assignment(
    assignment_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    row = get_assignment(db, assignment_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Assignment not found.")
    _require_own_learner(db, current_user, row.learner_id)

    delete_assignment(db, assignment_id)
    return {"deleted": True}


@router.post("/learners/{learner_id}/notes", response_model=NoteResponse)
def create_learner_note(
    learner_id: str,
    payload: NoteCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    _require_own_learner(db, current_user, learner_id)
    result = add_note(db, instructor_id=current_user.id, learner_id=learner_id, note=payload.note)
    return NoteResponse(**result)


@router.get("/learners/{learner_id}/notes", response_model=NoteListResponse)
def get_learner_notes(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    # Same "don't roster-gate reads" reasoning as list_learner_assignments.
    return {"notes": list_notes_for_learner(db, learner_id)}


@router.post("/learners/{learner_id}/certificates", response_model=CertificateResponse)
def issue_learner_certificate(
    learner_id: str,
    payload: IssueCertificateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    """Manual issuance — the "staff can also issue" path alongside
    sync_auto_certificates' automatic one. Roster-gated like assignments
    and notes (an admin is exempt via _require_own_learner)."""
    _require_own_learner(db, current_user, learner_id)
    try:
        certificate = issue_certificate_manually(db, learner_id, payload.course_id, current_user)
    except CertificateError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return certificate


@router.post("/certificates/{certificate_id}/revoke", response_model=CertificateResponse)
def revoke_learner_certificate(
    certificate_id: str,
    payload: RevokeCertificateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    """Corrects a wrongly-issued certificate without deleting it (see
    Certificate model docstring) — roster-gated by looking up the
    certificate's own learner first, same as delete_learner_assignment
    looks up its assignment's learner before checking ownership."""
    certificate = get_certificate(db, certificate_id)
    if certificate is None:
        raise HTTPException(status_code=404, detail="Certificate not found.")
    _require_own_learner(db, current_user, certificate.learner_id)

    updated = revoke_certificate(db, certificate_id, current_user, payload.reason)
    return updated
