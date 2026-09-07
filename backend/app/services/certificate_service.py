"""
Certification: a Certificate row per (learner, course) that has actually
reached that course's completion bar.

Deliberately NOT the same bar as course_catalog_service's progress_percent
(which counts anything "scored" — i.e. attempted with a real result, pass
or fail). A certificate is a real-world claim ("this person can do this"),
so it requires every item in the course's vocabulary to have been PASSED
at least once — see _course_completion_status below. Only the three
courses with both tracks_progress=True and built=True have a real
attempt table to check against; common-signs (no attempt tracking) and
workplace-communication (not built) are simply not certifiable yet, same
"real data or nothing" discipline as course_catalog_service itself.

Two ways a Certificate row comes to exist:
  - sync_auto_certificates(): called right after a qualifying attempt is
    saved (see routers/practice.py, motion_signs.py, word_signs.py) —
    issues a certificate the moment a learner's most recent attempt
    completes their last remaining item. issued_by="system".
  - issue_certificate_manually(): an instructor/admin issues one directly
    to a learner on their roster (instructor.py), regardless of whether
    the auto bar has been crossed — the "staff can also issue manually"
    path. Recorded with the staff member's own id/name, never disguised
    as an automatic issuance.

Either way, at most one certificate per (learner_id, course_id): a
second call is a no-op returning the existing row, so re-completing an
already-certified course (or double-clicking "issue") can't create
duplicates.
"""

import random
import string
import uuid
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.certificate import Certificate
from app.models.motion_sign_attempt import MotionSignAttempt
from app.models.practice_attempt import PracticeAttempt
from app.models.user import User
from app.models.word_sign_attempt import WordSignAttempt
from app.services.course_catalog_service import CATALOG
from app.services.gesture_recognition_service import get_supported_letters
from app.services.motion_sign_service import SUPPORTED_MOTION_SIGNS
from app.services.word_sign_service import get_supported_word_signs

VERIFICATION_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # no 0/O/1/I — avoids misreads
VERIFICATION_CODE_LENGTH = 10


def _course_attempt_config() -> dict:
    """
    Lazily built (not a module-level constant) since get_supported_word_signs()
    reads the trained model bundle off disk — calling it at import time
    would mean every module that imports certificate_service pays that
    cost even when it never touches word-sign courses.
    """
    return {
        "alphabet-fundamentals": (PracticeAttempt, PracticeAttempt.target_letter, get_supported_letters()),
        "everyday-gestures": (MotionSignAttempt, MotionSignAttempt.target_sign, list(SUPPORTED_MOTION_SIGNS)),
        "conversational-fluency": (WordSignAttempt, WordSignAttempt.target_word, get_supported_word_signs()),
    }


def _course_title(course_id: str) -> str:
    for course in CATALOG:
        if course["id"] == course_id:
            return course["title"]
    return course_id


def _course_completion_status(db: Session, learner_id: str, course_id: str) -> dict:
    """
    items_passed / items_total over the course's real vocabulary, using
    "at least one PASS on this item, ever" — not accuracy, not most-
    recent-attempt-only, since a single genuine pass is still real
    evidence the learner has done it correctly, and a certificate isn't
    trying to measure how consistently, just whether they can.
    """
    config = _course_attempt_config()
    if course_id not in config:
        return {"items_total": 0, "items_passed": 0, "eligible": False}

    model, target_column, supported_items = config[course_id]
    total = len(supported_items)
    if total == 0:
        return {"items_total": 0, "items_passed": 0, "eligible": False}

    passed_items = {
        row[0]
        for row in db.query(target_column)
        .filter(
            model.learner_id == learner_id,
            target_column.in_(supported_items),
            model.status == "pass",
        )
        .distinct()
        .all()
    }
    items_passed = len(passed_items)
    return {
        "items_total": total,
        "items_passed": items_passed,
        "eligible": items_passed >= total,
    }


def get_certifiable_courses_status(db: Session, learner_id: str) -> list[dict]:
    """Completion status for every course a certificate could exist for,
    plus whether one has already been issued — the learner-facing "what
    have I earned / what's left" view."""
    existing_by_course = {
        c.course_id: c
        for c in db.query(Certificate).filter(Certificate.learner_id == learner_id).all()
    }
    results = []
    for course_id in _course_attempt_config():
        status = _course_completion_status(db, learner_id, course_id)
        certificate = existing_by_course.get(course_id)
        results.append({
            "course_id": course_id,
            "course_title": _course_title(course_id),
            "items_total": status["items_total"],
            "items_passed": status["items_passed"],
            "eligible": status["eligible"],
            "already_issued": certificate is not None,
            "certificate_id": certificate.id if certificate else None,
        })
    return results


def _generate_verification_code(db: Session) -> str:
    # Collisions are astronomically unlikely at this alphabet/length, but
    # checked-and-retried anyway rather than assumed away — a verification
    # code silently colliding would be a real, if rare, correctness bug.
    for _ in range(10):
        code = "".join(random.choices(VERIFICATION_CODE_ALPHABET, k=VERIFICATION_CODE_LENGTH))
        if not db.query(Certificate).filter(Certificate.verification_code == code).first():
            return code
    raise RuntimeError("Could not generate a unique verification code.")


def _create_certificate(db: Session, learner_id: str, course_id: str, issued_by: str, issued_by_name: str) -> Certificate:
    certificate = Certificate(
        id=str(uuid.uuid4()),
        learner_id=learner_id,
        course_id=course_id,
        course_title=_course_title(course_id),
        verification_code=_generate_verification_code(db),
        issued_at=datetime.utcnow(),
        issued_by=issued_by,
        issued_by_name=issued_by_name,
    )
    db.add(certificate)
    db.commit()
    db.refresh(certificate)
    return certificate


def sync_auto_certificates(db: Session, learner_id: str, course_id: str) -> Certificate | None:
    """
    Call right after a qualifying attempt is saved for the given course.
    Scoped to one course_id (not all three) since the caller already
    knows which course the just-saved attempt belongs to — no reason to
    re-check the other two on every single attempt. Returns the newly
    issued Certificate, or None if not yet eligible or already certified.
    """
    if course_id not in _course_attempt_config():
        return None
    already = (
        db.query(Certificate)
        .filter(Certificate.learner_id == learner_id, Certificate.course_id == course_id)
        .first()
    )
    if already is not None:
        return None
    status = _course_completion_status(db, learner_id, course_id)
    if not status["eligible"]:
        return None
    return _create_certificate(db, learner_id, course_id, issued_by="system", issued_by_name="Automatically issued")


class CertificateError(Exception):
    pass


def issue_certificate_manually(db: Session, learner_id: str, course_id: str, issuer: User) -> Certificate:
    """
    Staff-initiated issuance — deliberately does NOT require
    _course_completion_status to say eligible=True first: an
    instructor/admin is allowed to certify a learner for a legitimate
    reason the automatic bar can't see (e.g. an in-person assessment),
    same trust extended to staff elsewhere in this codebase (assignments,
    notes). Still blocks a duplicate for the same (learner, course).
    """
    if course_id not in _course_attempt_config():
        raise CertificateError(f"'{course_id}' isn't a certifiable course.")
    learner = db.query(User).filter(User.id == learner_id, User.role == "learner").first()
    if learner is None:
        raise CertificateError("No learner found with that id.")
    already = (
        db.query(Certificate)
        .filter(Certificate.learner_id == learner_id, Certificate.course_id == course_id)
        .first()
    )
    if already is not None:
        raise CertificateError("This learner already has a certificate for this course.")
    return _create_certificate(db, learner_id, course_id, issued_by=issuer.id, issued_by_name=issuer.name)


def list_certificates_for_learner(db: Session, learner_id: str) -> list[Certificate]:
    return (
        db.query(Certificate)
        .filter(Certificate.learner_id == learner_id)
        .order_by(Certificate.issued_at.desc())
        .all()
    )


def get_certificate(db: Session, certificate_id: str) -> Certificate | None:
    return db.query(Certificate).filter(Certificate.id == certificate_id).first()


def get_certificate_by_code(db: Session, verification_code: str) -> Certificate | None:
    # Case/whitespace-insensitive: someone reading a code off a printed
    # certificate or retyping it shouldn't get a false "not found" over
    # a lowercase letter or a stray space.
    normalized = verification_code.strip().upper()
    return db.query(Certificate).filter(Certificate.verification_code == normalized).first()


def revoke_certificate(db: Session, certificate_id: str, revoked_by: User, reason: str | None) -> Certificate | None:
    certificate = get_certificate(db, certificate_id)
    if certificate is None:
        return None
    certificate.revoked = True
    certificate.revoked_at = datetime.utcnow()
    certificate.revoked_by = revoked_by.id
    certificate.revoked_reason = reason
    db.commit()
    db.refresh(certificate)
    return certificate
