"""
Seed a demo learner straight to a completed course + issued certificate,
for presentation/demo purposes — skips clicking through the actual
Wave/Clap camera capture flow in the UI.

Targets "everyday-gestures" (Motion Signs) because it's the smallest
certifiable course: SUPPORTED_MOTION_SIGNS is just ["Wave", "Clap"], so
one passing MotionSignAttempt per sign is enough to cross the real
completion bar in certificate_service._course_completion_status (see that
file — "every item passed at least once", not fabricated by directly
inserting a Certificate row).

Usage (from backend/, with the venv active, same DB the app itself uses):
    python scripts/seed_demo_certificate.py [email]

Defaults to demo.learner@example.com. The user must already exist (sign
up in the app first, or use scripts/... instructor tools) — this script
does not create accounts, only attempt/certificate data for one.
"""

import sys
import uuid
from datetime import datetime

sys.path.insert(0, ".")

from app.database import SessionLocal  # noqa: E402
from app.models.motion_sign_attempt import MotionSignAttempt  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.certificate_service import (  # noqa: E402
    get_certifiable_courses_status,
    sync_auto_certificates,
)
from app.services.motion_sign_service import SUPPORTED_MOTION_SIGNS  # noqa: E402

COURSE_ID = "everyday-gestures"


def seed(email: str) -> None:
    db = SessionLocal()
    try:
        learner = db.query(User).filter(User.email == email).first()
        if learner is None:
            print(f"No user found with email {email!r}. Register that account in the app first, then rerun this.")
            return
        if learner.role != "learner":
            print(f"{email} is a {learner.role} account, not a learner — certificates only apply to learners.")
            return

        for sign in SUPPORTED_MOTION_SIGNS:
            already_passed = (
                db.query(MotionSignAttempt)
                .filter(
                    MotionSignAttempt.learner_id == learner.id,
                    MotionSignAttempt.target_sign == sign,
                    MotionSignAttempt.status == "pass",
                )
                .first()
            )
            if already_passed:
                print(f"  {sign}: already has a passing attempt, leaving it alone.")
                continue

            attempt = MotionSignAttempt(
                id=str(uuid.uuid4()),
                learner_id=learner.id,
                target_sign=sign,
                predicted_sign=sign,
                status="pass",
                correct=True,
                confidence=None,  # rule-based detector never populates this — see model docstring
                frame_count=24,
                created_at=datetime.utcnow(),
            )
            db.add(attempt)
            db.commit()
            print(f"  {sign}: seeded a passing attempt.")

        certificate = sync_auto_certificates(db, learner.id, COURSE_ID)
        if certificate:
            print(f"\nCertificate issued: {certificate.course_title}")
            print(f"Verification code: {certificate.verification_code}")
        else:
            existing = next(
                (c for c in get_certifiable_courses_status(db, learner.id) if c["course_id"] == COURSE_ID),
                None,
            )
            if existing and existing["already_issued"]:
                print(f"\n{email} already had a certificate for {COURSE_ID} — nothing new to issue.")
            else:
                print(f"\nSomething unexpected: still not eligible for {COURSE_ID} after seeding. Status: {existing}")

        print("\nFull certification status for this learner:")
        for status in get_certifiable_courses_status(db, learner.id):
            marker = "✓ issued" if status["already_issued"] else ("eligible, not yet issued" if status["eligible"] else "not yet eligible")
            print(f"  - {status['course_title']}: {status['items_passed']}/{status['items_total']} passed — {marker}")
    finally:
        db.close()


if __name__ == "__main__":
    target_email = sys.argv[1] if len(sys.argv) > 1 else "demo.learner@example.com"
    print(f"Seeding demo completion for {target_email} on course {COURSE_ID!r}...")
    seed(target_email)
