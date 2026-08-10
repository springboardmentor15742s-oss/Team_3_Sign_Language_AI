from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.analytics import LearnerAnalyticsResponse
from app.schemas.learning_plan import LearningPlanResponse
from app.schemas.recommendation import RecommendationsResponse
from app.services.auth_dependency import require_self_or_staff
from app.services.learning_analytics_service import get_learner_analytics
from app.services.learning_plan_service import generate_learning_plan
from app.services.recommendation_service import get_recommendations

router = APIRouter(prefix="/api/learner", tags=["Learner Analytics"])

@router.get("/{learner_id}/analytics", response_model=LearnerAnalyticsResponse)
def get_analytics(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    return get_learner_analytics(db, learner_id)

@router.get("/{learner_id}/recommendations", response_model=RecommendationsResponse)
def get_learner_recommendations(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    return get_recommendations(db, learner_id)

@router.get("/{learner_id}/learning-plan", response_model=LearningPlanResponse)
def get_learner_learning_plan(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    return generate_learning_plan(db, learner_id)
