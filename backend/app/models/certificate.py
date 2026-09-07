from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String
from datetime import datetime
from app.database import Base


class Certificate(Base):
    """
    One row per (learner, course) that has actually reached that
    course's real completion bar (see certificate_service.py for the
    "every item passed at least once" definition — deliberately
    stricter than the "attempted" progress_percent shown elsewhere in
    the app). Issued either automatically by the system the moment a
    learner crosses that bar, or manually by an instructor/admin
    (issued_by holds "system" or that staff member's user id, so a
    certificate always says honestly how it came to exist).

    course_title is a snapshot at issue time, not a live join against
    course_catalog_service.CATALOG — if a course's title ever changes,
    an already-issued certificate keeps reading the title it was
    actually earned under.

    verification_code is a short, unique, human-shareable code (not the
    row id) so a certificate can be looked up by anyone — an employer,
    say — without needing to guess or leak an internal id; see
    GET /api/certificates/verify/{code} (no auth required).

    revoked/revoked_at/revoked_by/revoked_reason exist because
    certification is a real-world claim: an admin needs a way to correct
    a wrongly-issued certificate without deleting the historical record
    (deleting would let the same course be "completed" again silently
    and would destroy the audit trail a revoked certificate itself is
    part of).
    """

    __tablename__ = "certificates"

    id = Column(String, primary_key=True)
    learner_id = Column(String, ForeignKey("users.id"), nullable=False)
    course_id = Column(String, nullable=False)
    course_title = Column(String, nullable=False)

    verification_code = Column(String, unique=True, index=True, nullable=False)

    issued_at = Column(DateTime, default=datetime.utcnow)
    issued_by = Column(String, nullable=False)  # "system" or a staff user's id
    issued_by_name = Column(String, nullable=False)  # "Automatically issued" or that staff member's name

    revoked = Column(Boolean, default=False, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    revoked_by = Column(String, nullable=True)
    revoked_reason = Column(String, nullable=True)
