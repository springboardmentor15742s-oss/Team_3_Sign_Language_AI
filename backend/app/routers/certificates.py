from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.certificate import (
    CertificateListResponse,
    CertificateResponse,
    CertificateVerificationResponse,
    CertificationStatusResponse,
)
from app.services.auth_dependency import require_self_or_staff
from app.services.certificate_service import (
    get_certificate,
    get_certificate_by_code,
    get_certifiable_courses_status,
    list_certificates_for_learner,
    sync_auto_certificates,
)

router = APIRouter(prefix="/api/certificates", tags=["Certificates"])


@router.get("/learner/{learner_id}", response_model=CertificateListResponse)
def get_learner_certificates(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    """
    Also runs the auto-issuance check for every certifiable course before
    listing — a safety net/backfill, not just a read: a learner who
    completed a course's real vocabulary before this feature existed (or
    whose completing attempt happened to race this check) still gets
    their certificate the next time this page loads, not never.
    """
    for status in get_certifiable_courses_status(db, learner_id):
        if status["eligible"] and not status["already_issued"]:
            sync_auto_certificates(db, learner_id, status["course_id"])
    return {"certificates": list_certificates_for_learner(db, learner_id)}


@router.get("/learner/{learner_id}/status", response_model=CertificationStatusResponse)
def get_learner_certification_status(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    """Progress toward every certifiable course, whether earned yet or
    not — same "show real progress, never hide it" discipline as
    course_catalog_service and progress_service."""
    return {"courses": get_certifiable_courses_status(db, learner_id)}


@router.get("/learner/{learner_id}/{certificate_id}/pdf")
def download_certificate_pdf(
    learner_id: str,
    certificate_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    # Imported here (not at module load) only to avoid pulling reportlab
    # into every request to this router's other, more-frequently-hit
    # endpoints — the PDF renderer is the one path that needs it.
    from app.services.certificate_pdf_service import render_certificate_pdf

    certificate = get_certificate(db, certificate_id)
    if certificate is None or certificate.learner_id != learner_id:
        raise HTTPException(status_code=404, detail="Certificate not found.")

    learner = db.query(User).filter(User.id == learner_id).first()
    if learner is None:
        raise HTTPException(status_code=404, detail="Learner not found.")

    pdf_bytes = render_certificate_pdf(CertificateResponse.model_validate(certificate), learner.name)
    filename = f"certificate-{certificate.course_id}-{certificate.verification_code}.pdf"
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/verify/{verification_code}", response_model=CertificateVerificationResponse)
def verify_certificate(verification_code: str, db: Session = Depends(get_db)):
    """
    Deliberately no auth — the whole point of a verification code is
    that anyone holding one (an employer, say) can confirm it's real
    without a platform account. Returns valid=False rather than a 404
    for an unknown code, since "not found" and "not valid" read the same
    to a verifier and a 404 would need frontend-specific error handling
    a plain 200 response doesn't.
    """
    certificate = get_certificate_by_code(db, verification_code)
    if certificate is None:
        return CertificateVerificationResponse(valid=False)

    learner = db.query(User).filter(User.id == certificate.learner_id).first()
    return CertificateVerificationResponse(
        valid=not certificate.revoked,
        learner_name=learner.name if learner else "(unknown learner)",
        course_title=certificate.course_title,
        issued_at=certificate.issued_at,
        revoked=certificate.revoked,
        revoked_at=certificate.revoked_at,
    )
