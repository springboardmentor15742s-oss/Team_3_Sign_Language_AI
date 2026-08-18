from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.practice_attempt import PracticeAttempt

TOP_N_PAIRS = 5


def get_confusion_pairs(db: Session, learner_id: str) -> dict:
    """
    Aggregates target/predicted letter pairs from a learner's failed
    attempts — which letter a target most often gets misread as —
    ordered by how often each pair occurred, top TOP_N_PAIRS only.
    """
    rows = (
        db.query(
            PracticeAttempt.target_letter,
            PracticeAttempt.predicted_letter,
            func.count(PracticeAttempt.id).label("pair_count"),
        )
        .filter(
            PracticeAttempt.learner_id == learner_id,
            PracticeAttempt.status == "fail",
        )
        .group_by(PracticeAttempt.target_letter, PracticeAttempt.predicted_letter)
        .order_by(func.count(PracticeAttempt.id).desc())
        .limit(TOP_N_PAIRS)
        .all()
    )

    return {
        "learner_id": learner_id,
        "pairs": [
            {"target_letter": target, "predicted_letter": predicted, "count": count}
            for target, predicted, count in rows
        ],
    }
