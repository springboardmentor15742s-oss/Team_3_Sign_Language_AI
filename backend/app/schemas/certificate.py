from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

MAX_REVOKE_REASON_LENGTH = 1000


class CertificateResponse(BaseModel):
    id: str
    learner_id: str
    course_id: str
    course_title: str
    verification_code: str
    issued_at: datetime
    issued_by: str
    issued_by_name: str
    revoked: bool
    revoked_at: Optional[datetime] = None
    revoked_reason: Optional[str] = None

    class Config:
        from_attributes = True


class CertificateListResponse(BaseModel):
    certificates: list[CertificateResponse]


class CourseCertificationStatus(BaseModel):
    course_id: str
    course_title: str
    items_total: int
    items_passed: int
    eligible: bool
    already_issued: bool
    certificate_id: Optional[str] = None


class CertificationStatusResponse(BaseModel):
    courses: list[CourseCertificationStatus]


class IssueCertificateRequest(BaseModel):
    course_id: str


class RevokeCertificateRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=MAX_REVOKE_REASON_LENGTH)


class CertificateVerificationResponse(BaseModel):
    valid: bool
    # None only when valid=False because no certificate with that code
    # exists at all — a revoked-but-real certificate still returns every
    # other field, with valid=False and revoked=True, so a verifier can
    # tell "never existed" apart from "existed, later revoked".
    learner_name: Optional[str] = None
    course_title: Optional[str] = None
    issued_at: Optional[datetime] = None
    revoked: bool = False
    revoked_at: Optional[datetime] = None
