"""
Certification routes — Milestone 4 ("Implement Certification Workflows").

    GET  /api/certification/eligibility            current user's progress against all 4 levels
    POST /api/certification/issue/{level}           issue a certificate if eligible
    GET  /api/certification/my                      current user's issued certificates
    GET  /api/certification/{cert_id}/download       plain-text certificate download
    GET  /api/certification/{cert_id}/download/pdf   polished PDF certificate download
    GET  /api/certification/verify/{code}            PUBLIC — verify a certificate by its code
    GET  /api/certification/all                      Instructor/Administrator — platform-wide list
"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse, Response

from certification.rules import (
    LEVELS,
    check_all_levels,
    check_eligibility,
    generate_certificate_code,
    render_certificate_text,
)
from certification.pdf_certificate import build_certificate_pdf
from database import db
from deps import get_current_user, require_roles
from intelligence.analytics import compute_analytics
from notifications.service import notify_achievement
from schemas.models import CertificateStatusUpdateRequest

router = APIRouter(prefix="/api/certification", tags=["certification"])

CERT_STATUSES = ("Active", "Revoked")


def _get_authorized_certificate(cert_id: int, current_user: dict) -> dict:
    cert = db.get_certificate_by_id(cert_id)
    if not cert:
        raise HTTPException(status_code=404, detail="Certificate not found.")
    if cert["user_id"] != current_user["id"] and current_user["role"] not in ("Instructor", "Administrator"):
        raise HTTPException(status_code=403, detail="Not your certificate.")
    return cert


@router.get("/eligibility")
def eligibility(current_user=Depends(get_current_user)):
    analytics = compute_analytics(current_user["id"])
    return {"levels": check_all_levels(analytics)}


@router.post("/issue/{level}")
def issue_certificate(level: str, current_user=Depends(get_current_user)):
    if level not in LEVELS:
        raise HTTPException(status_code=400, detail=f"Unknown level. Choose one of: {', '.join(LEVELS)}")

    if db.user_already_has_active_certificate(current_user["id"], level):
        raise HTTPException(status_code=409, detail=f"You already hold an active {level} certificate.")

    analytics = compute_analytics(current_user["id"])
    result = check_eligibility(analytics, level)
    if not result["eligible"]:
        raise HTTPException(
            status_code=400,
            detail={"message": "Not yet eligible for this certificate.", "reasons": result["reasons"]},
        )

    code = generate_certificate_code(current_user["id"], level)
    cert = db.create_certificate(
        current_user["id"],
        code,
        level,
        analytics["overall_accuracy"],
        analytics["total_attempts"],
        len(analytics["by_gesture"]),
    )
    cert["username"] = current_user["username"]
    notify_achievement(current_user["id"], level, code)
    return cert


@router.get("/my")
def my_certificates(current_user=Depends(get_current_user)):
    return db.get_user_certificates(current_user["id"])


@router.get("/{cert_id}/download")
def download_certificate(cert_id: int, current_user=Depends(get_current_user)):
    cert = _get_authorized_certificate(cert_id, current_user)
    text = render_certificate_text(cert)
    filename = f"{cert['certificate_code']}.txt"
    return PlainTextResponse(
        content=text, headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )


@router.get("/{cert_id}/download/pdf")
def download_certificate_pdf(cert_id: int, current_user=Depends(get_current_user)):
    """The 'real' certificate download — a polished, LinkedIn-style landscape
    PDF (see certification/pdf_certificate.py) suitable for sharing with an
    employer, not just a plain-text confirmation."""
    cert = _get_authorized_certificate(cert_id, current_user)
    pdf_bytes = build_certificate_pdf(cert)
    filename = f"{cert['certificate_code']}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/verify/{code}")
def verify_certificate(code: str):
    """Public — no auth required, so anyone with a certificate code (e.g. an
    employer) can confirm it's genuine and still active."""
    cert = db.get_certificate_by_code(code)
    if not cert:
        return {"valid": False, "message": "No certificate found with that code."}
    return {
        "valid": cert["status"] == "Active",
        "username": cert["username"],
        "level": cert["level"],
        "issued_at": cert["issued_at"],
        "status": cert["status"],
        "overall_accuracy": cert["overall_accuracy"],
    }


@router.get("/all")
def all_certificates(current_user=Depends(require_roles("Instructor", "Administrator", "Accessibility Trainer"))):
    """Certification monitoring — platform-wide list for the Instructor /
    Accessibility Trainer / Admin dashboards."""
    return db.get_all_certificates()


@router.put("/{cert_id}/status")
def update_certificate_status(
    cert_id: int,
    payload: CertificateStatusUpdateRequest,
    current_user=Depends(require_roles("Administrator")),
):
    """Certificate revocation (and reactivation) — Administrator only. The
    `status` column has supported 'Revoked' since Milestone 4; this is the
    admin action that actually uses it."""
    if payload.status not in CERT_STATUSES:
        raise HTTPException(status_code=400, detail=f"Status must be one of: {', '.join(CERT_STATUSES)}")
    if not db.get_certificate_by_id(cert_id):
        raise HTTPException(status_code=404, detail="Certificate not found.")
    return db.update_certificate_status(cert_id, payload.status)
