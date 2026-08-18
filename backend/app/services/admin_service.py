from sqlalchemy.orm import Session

from app.models.user import User
from app.services.learning_analytics_service import get_learner_analytics


def get_admin_overview(db: Session) -> dict:
    """
    Builds a platform-wide overview for admins: totals across every user
    and every learner's practice history, plus a full user list.

    Reuses learning_analytics_service.get_learner_analytics() per
    learner (same pattern as instructor_service.get_learner_roster())
    rather than re-deriving attempt/accuracy math — both the per-learner
    attempts figure in the user list and the platform-wide accuracy
    roll-up are built from the same already-established source of truth,
    computed once per learner.
    """
    users = db.query(User).order_by(User.created_at).all()

    role_counts: dict[str, int] = {}
    for user in users:
        role_counts[user.role] = role_counts.get(user.role, 0) + 1

    total_attempts = 0
    total_correct = 0
    total_incorrect = 0

    user_list = []
    for user in users:
        # Non-learner roles don't practice, so there's nothing to
        # aggregate — null, not 0, so it reads as "not applicable".
        attempts_for_user = None
        if user.role == "learner":
            analytics = get_learner_analytics(db, user.id)
            attempts_for_user = analytics["total_attempts"]
            total_attempts += analytics["total_attempts"]
            total_correct += analytics["correct_count"]
            total_incorrect += analytics["incorrect_count"]

        user_list.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "created_at": user.created_at,
            "total_attempts": attempts_for_user,
        })

    scored = total_correct + total_incorrect
    overall_accuracy_percent = round(total_correct / scored * 100, 1) if scored > 0 else None

    return {
        "total_users": len(users),
        "role_counts": role_counts,
        "total_practice_attempts": total_attempts,
        "overall_accuracy_percent": overall_accuracy_percent,
        "users": user_list,
    }
