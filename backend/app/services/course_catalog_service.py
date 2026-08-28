"""
A small, honest course catalog. This platform has no course/lesson data
model — "courses" here map directly to what's actually built: alphabet
practice (real, with real progress computed from PracticeAttempt data),
the common-signs tester (real, but not attempt-tracked, so no progress
bar — just an entry point), everyday-gestures (real, rule-based motion
detection over a hand-landmark sequence, attempt-tracked via
MotionSignAttempt), and now conversational-fluency (real, a trained
temporal classifier over MS-ASL video data, attempt-tracked via
WordSignAttempt — see word_sign_service.py / scripts/train_msasl_classifier.py).

conversational-fluency ships with an honest caveat rather than a silent
quality drop: real experiments (scripts/improve_msasl_classifier.py,
scripts/vocab_reduction_experiment.py) found the trained-model approach
that works for the alphabet doesn't transfer cleanly to word signs on
this little real data — augmenting/re-featuring all 30 MS-ASL
"intermediate" words only got test accuracy from 32.5% to ~34%, so the
vocabulary was cut to the 16 words with enough real clips per word
(>=15), which got a genuinely better 49% test accuracy. That's real
progress over the fully-locked state, but still well below the
alphabet/common-signs classifiers' reliability — locked_reason-style
framing is kept in the description for that reason, and the frontend
surfaces the model's own test_accuracy so this isn't presented as more
reliable than it is.

workplace-communication stays locked: it would need its own downloaded
MS-ASL vocabulary tier and trained model, and no workplace-specific
clips have been collected yet — the same "not built, stated reason"
discipline this catalog already used for both tiers before
conversational-fluency's model existed.
"""

from sqlalchemy.orm import Session

from app.models.motion_sign_attempt import MotionSignAttempt
from app.models.word_sign_attempt import WordSignAttempt
from app.services.common_signs_service import SUPPORTED_SIGNS
from app.services.motion_sign_service import SUPPORTED_MOTION_SIGNS
from app.services.word_sign_service import get_model_info, get_supported_word_signs

_NOT_BUILT_REASON = (
    "Needs its own downloaded video-sign dataset and a trained temporal model for this "
    "vocabulary tier — not built yet. (See Intermediate Conversational Fluency for what that "
    "looks like once it exists: a real trained classifier, not rules.)"
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
        "description": (
            "16 real conversational words, recognized by a classifier trained on real MS-ASL "
            "video clips — a smaller, more reliable vocabulary rather than the full 30-word set "
            "the earlier dataset attempt couldn't support well (see the practice page for the "
            "model's own measured accuracy)."
        ),
        "route": "/conversational-fluency",
        "built": True,
        "tracks_progress": True,
        "locked_reason": None,
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
        entry["model_test_accuracy"] = None

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
        elif course["id"] == "conversational-fluency":
            supported_words = get_supported_word_signs()
            total = len(supported_words)
            entry["item_count"] = total
            if db is not None and learner_id is not None:
                scored_words = {
                    row[0]
                    for row in db.query(WordSignAttempt.target_word)
                    .filter(
                        WordSignAttempt.learner_id == learner_id,
                        WordSignAttempt.target_word.in_(supported_words),
                        WordSignAttempt.status != "no_attempt_detected",
                    )
                    .distinct()
                    .all()
                }
                entry["progress_percent"] = round((len(scored_words) / total) * 100, 1) if total else None
            entry["model_test_accuracy"] = get_model_info()["test_accuracy"]

        courses.append(entry)
    return courses
