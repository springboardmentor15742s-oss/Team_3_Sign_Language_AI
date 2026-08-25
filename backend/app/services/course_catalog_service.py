"""
A small, honest course catalog. This platform has no course/lesson data
model — "courses" here map directly to what's actually built: alphabet
practice (real, with real progress computed from PracticeAttempt data),
the common-signs tester (real, but not attempt-tracked, so no progress
bar — just an entry point), and everyday-gestures (real, rule-based
motion detection over a hand-landmark sequence, attempt-tracked via
MotionSignAttempt). The remaining categories are explicitly marked
built=False with a stated reason rather than given a fabricated progress
percentage, matching this project's documented scope (see SECURITY.md /
the About modal): the full ASL vocabulary those tiers need is
video-sequence content that has to come from a real downloaded dataset
and a trained temporal model, not rules — everyday-gestures proves the
motion-capture pipeline works, but Wave/Clap are generic gestures, not
ASL signs, so they don't count as progress on these two tiers.
"""

from sqlalchemy.orm import Session

from app.models.motion_sign_attempt import MotionSignAttempt
from app.services.common_signs_service import SUPPORTED_SIGNS
from app.services.motion_sign_service import SUPPORTED_MOTION_SIGNS

_NOT_BUILT_REASON = (
    "Needs a real downloaded video-sign dataset and a trained temporal model for the full ASL "
    "vocabulary — not built yet. (The motion-capture pipeline itself now works — see Everyday "
    "Gestures — but that's rule-based Wave/Clap detection, not trained ASL vocabulary.)"
)

CATALOG: list[dict] = [
    {
        "id": "alphabet-fundamentals",
        "title": "ASL Alphabet Fundamentals",
        "category": "Beginner Sign Language",
        "description": "Practice static ASL alphabet handshapes with instant feedback from the trained classifier.",
        "route": "/practice",
        "built": True,
        "tracks_progress": True,
        "locked_reason": None,
    },
    {
        "id": "common-signs",
        "title": "Common Signs",
        "category": "Everyday Communication",
        "description": "A small set of common static-handshape signs, recognized with rule-based hand geometry.",
        "route": "/common-signs",
        "built": True,
        "tracks_progress": False,
        "locked_reason": None,
    },
    {
        "id": "everyday-gestures",
        "title": "Everyday Gestures",
        "category": "Everyday Communication",
        "description": "Generic motion gestures (Wave, Clap), recognized from real hand-trajectory geometry across a short video clip — this platform's first motion-based (not single-frame) recognizer.",
        "route": "/motion-signs",
        "built": True,
        "tracks_progress": True,
        "locked_reason": None,
    },
    {
        "id": "conversational-fluency",
        "title": "Intermediate Conversational Fluency",
        "category": "Intermediate Sign Language",
        "description": "Full-word and motion-based conversational signing.",
        "route": None,
        "built": False,
        "tracks_progress": False,
        "locked_reason": _NOT_BUILT_REASON,
    },
    {
        "id": "workplace-communication",
        "title": "Professional & Workplace Communication",
        "category": "Professional Communication",
        "description": "Workplace-specific vocabulary and phrases.",
        "route": None,
        "built": False,
        "tracks_progress": False,
        "locked_reason": _NOT_BUILT_REASON,
    },
]


def get_course_catalog(analytics: dict | None, db: Session | None = None, learner_id: str | None = None) -> list[dict]:
    """
    Returns CATALOG with real progress_percent filled in where it's
    computable (alphabet-fundamentals, from analytics.per_letter;
    everyday-gestures, from real MotionSignAttempt rows when db+learner_id
    are given); every other course gets progress_percent=None rather than
    an invented number.
    """
    courses = []
    for course in CATALOG:
        entry = dict(course)
        entry["progress_percent"] = None
        entry["item_count"] = None

        if course["id"] == "alphabet-fundamentals" and analytics is not None:
            per_letter = analytics["per_letter"]
            total = len(per_letter)
            scored = sum(1 for stats in per_letter.values() if stats["accuracy_percent"] is not None)
            entry["progress_percent"] = round((scored / total) * 100, 1) if total else None
            entry["item_count"] = total
        elif course["id"] == "common-signs":
            entry["item_count"] = len(SUPPORTED_SIGNS)
        elif course["id"] == "everyday-gestures":
            total = len(SUPPORTED_MOTION_SIGNS)
            entry["item_count"] = total
            if db is not None and learner_id is not None:
                scored_signs = {
                    row[0]
                    for row in db.query(MotionSignAttempt.target_sign)
                    .filter(
                        MotionSignAttempt.learner_id == learner_id,
                        MotionSignAttempt.target_sign.in_(SUPPORTED_MOTION_SIGNS),
                        MotionSignAttempt.status != "no_attempt_detected",
                    )
                    .distinct()
                    .all()
                }
                entry["progress_percent"] = round((len(scored_signs) / total) * 100, 1) if total else None

        courses.append(entry)
    return courses
