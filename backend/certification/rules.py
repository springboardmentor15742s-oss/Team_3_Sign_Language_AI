"""
Certification Workflows — Milestone 4 (Week 7 & 8, Certification, Testing &
Deployment).

Reuses Milestone 3's `compute_analytics()` as its single source of truth —
a certificate is only ever issued if the learner's *live* analytics clear
the bar for that level, so eligibility can never drift out of sync with
what the Dashboard already shows.

Four certification levels, matching the roadmap's "Assessment Levels":
Beginner, Intermediate, Advanced, Professional. Each has three checks:
  - minimum total practice attempts logged
  - minimum overall accuracy
  - minimum number of *distinct* gestures practiced
Advanced and Professional additionally require zero remaining weak areas
(every practiced gesture must be at "Good" level) — you shouldn't be able
to certify at an advanced level while still failing basic signs.
"""
import hashlib
import secrets
from datetime import datetime, timezone

LEVELS = ["Beginner", "Intermediate", "Advanced", "Professional"]

REQUIREMENTS = {
    "Beginner": {"min_attempts": 5, "min_accuracy": 60.0, "min_gestures": 3, "require_no_weak_areas": False},
    "Intermediate": {"min_attempts": 15, "min_accuracy": 75.0, "min_gestures": 5, "require_no_weak_areas": False},
    "Advanced": {"min_attempts": 30, "min_accuracy": 85.0, "min_gestures": 8, "require_no_weak_areas": True},
    "Professional": {"min_attempts": 50, "min_accuracy": 92.0, "min_gestures": 10, "require_no_weak_areas": True},
}


def check_eligibility(analytics: dict, level: str) -> dict:
    """
    Returns {eligible: bool, level, requirements: {...}, progress: {...},
    reasons: [str, ...]} — `reasons` is empty when eligible, otherwise it
    lists exactly which requirement(s) are still unmet, so the frontend can
    show a concrete checklist instead of a flat pass/fail.
    """
    req = REQUIREMENTS[level]
    total_attempts = analytics.get("total_attempts", 0)
    overall_accuracy = analytics.get("overall_accuracy", 0.0)
    gestures_practiced = len(analytics.get("by_gesture", []))
    weak_areas = analytics.get("weak_areas", [])

    reasons = []
    if total_attempts < req["min_attempts"]:
        reasons.append(f"Needs {req['min_attempts']} practice attempts (have {total_attempts})")
    if overall_accuracy < req["min_accuracy"]:
        reasons.append(f"Needs {req['min_accuracy']}% overall accuracy (have {overall_accuracy}%)")
    if gestures_practiced < req["min_gestures"]:
        reasons.append(f"Needs {req['min_gestures']} distinct gestures practiced (have {gestures_practiced})")
    if req["require_no_weak_areas"] and weak_areas:
        names = ", ".join(g["display_name"] for g in weak_areas)
        reasons.append(f"All practiced gestures must reach 'Good' level (still weak: {names})")

    return {
        "level": level,
        "eligible": len(reasons) == 0,
        "requirements": req,
        "progress": {
            "total_attempts": total_attempts,
            "overall_accuracy": overall_accuracy,
            "gestures_practiced": gestures_practiced,
            "weak_area_count": len(weak_areas),
        },
        "reasons": reasons,
    }


def check_all_levels(analytics: dict) -> list:
    return [check_eligibility(analytics, level) for level in LEVELS]


def generate_certificate_code(user_id: int, level: str) -> str:
    """Short, unique, non-guessable code used for public verification."""
    salt = secrets.token_hex(4)
    raw = f"{user_id}:{level}:{datetime.now(timezone.utc).isoformat()}:{salt}"
    digest = hashlib.sha256(raw.encode()).hexdigest()[:10].upper()
    return f"SLP-{level[:3].upper()}-{digest}"


def render_certificate_text(cert: dict) -> str:
    """Plain-text printable certificate (frontend also offers browser Print
    → Save as PDF for a formatted version — see Certifications.jsx)."""
    lines = [
        "=" * 60,
        "SIGN LANGUAGE LEARNING & ASSESSMENT PLATFORM",
        "CERTIFICATE OF COMPLETION",
        "=" * 60,
        "",
        f"This certifies that:  {cert['username']}",
        f"has achieved the:    {cert['level']} level",
        "",
        f"Overall accuracy:     {cert['overall_accuracy']}%",
        f"Practice attempts:    {cert['total_attempts']}",
        f"Gestures certified:   {cert['gestures_certified']}",
        "",
        f"Certificate code:     {cert['certificate_code']}",
        f"Issued:               {cert['issued_at']}",
        f"Status:               {cert['status']}",
        "",
        "Verify this certificate at:",
        f"  /api/certification/verify/{cert['certificate_code']}",
        "=" * 60,
    ]
    return "\n".join(lines)
