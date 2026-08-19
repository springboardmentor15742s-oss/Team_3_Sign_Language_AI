from datetime import datetime

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.report import (
    LearnerReport,
    ReportConfusionPair,
    ReportLetterStats,
    ReportRecommendation,
    ReportWeakArea,
)
from app.services.confusion_service import get_confusion_pairs
from app.services.feedback_service import generate_feedback
from app.services.learning_analytics_service import (
    WEAK_AREA_ACCURACY_THRESHOLD,
    WEAK_AREA_MIN_SCORED_ATTEMPTS,
    get_learner_analytics,
)
from app.services.recommendation_service import get_recommendations


def assemble_learner_report(db: Session, learner_id: str) -> LearnerReport:
    """
    Assembles everything a learner progress report needs by calling the
    existing analytics/recommendation/confusion/feedback services — no
    parallel aggregation logic. Pure data assembly; PDF rendering is a
    separate stage.
    """
    learner = db.query(User).filter(User.id == learner_id).first()
    if learner is None:
        raise ValueError(f"No such learner: {learner_id}")

    analytics = get_learner_analytics(db, learner_id)
    recommendations = get_recommendations(db, learner_id)["recommendations"]
    confusion_pairs = get_confusion_pairs(db, learner_id)["pairs"]

    per_letter = [
        ReportLetterStats(
            letter=letter,
            attempts=stats["attempts"],
            accuracy_percent=stats["accuracy_percent"],
        )
        for letter, stats in analytics["per_letter"].items()
    ]
    letters_scored = sum(1 for entry in per_letter if entry.accuracy_percent is not None)

    weak_areas = [
        ReportWeakArea(
            letter=w["letter"],
            accuracy_percent=w["accuracy_percent"],
            scored_attempts=w["scored_attempts"],
            # Reuses the exact corrective text shown during live practice
            # for a "fail" — same wording, not a separately-maintained copy.
            note=generate_feedback({"status": "fail", "target_letter": w["letter"]}),
        )
        for w in analytics["weak_areas"]
    ]

    return LearnerReport(
        learner_id=learner.id,
        learner_name=learner.name,
        learner_email=learner.email,
        generated_at=datetime.utcnow(),
        total_attempts=analytics["total_attempts"],
        scored_attempts=analytics["scored_attempts"],
        overall_accuracy_percent=analytics["overall_accuracy_percent"],
        letters_scored=letters_scored,
        total_letters=len(per_letter),
        per_letter=per_letter,
        weak_areas=weak_areas,
        recommendations=[ReportRecommendation(**r) for r in recommendations],
        confusion_pairs=[ReportConfusionPair(**p) for p in confusion_pairs],
        weak_area_accuracy_threshold=WEAK_AREA_ACCURACY_THRESHOLD,
        weak_area_min_scored_attempts=WEAK_AREA_MIN_SCORED_ATTEMPTS,
    )
