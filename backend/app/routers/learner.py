from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.analytics import LearnerAnalyticsResponse
from app.schemas.adaptive_learning import AdaptiveLearningPlanResponse
from app.schemas.confusion import ConfusionPairsResponse
from app.schemas.courses import CourseCatalogResponse
from app.schemas.feedback import LearnerFeedbackResponse
from app.schemas.learning_plan import LearningPlanResponse
from app.schemas.progress import LearnerProgressResponse
from app.schemas.recommendation import RecommendationsResponse
from app.services.ai_feedback_service import get_learner_feedback
from app.services.auth_dependency import require_self_or_staff
from app.services.confusion_service import get_confusion_pairs
from app.services.course_catalog_service import get_course_catalog
from app.services.learning_analytics_service import get_learner_analytics
from app.services.adaptive_learning_service import get_adaptive_learning_plan
from app.services.learning_plan_service import generate_learning_plan
from app.services.progress_service import get_learner_progress
from app.services.recommendation_service import get_recommendations

router = APIRouter(prefix="/api/learner", tags=["Learner Analytics"])

@router.get("/{learner_id}/adaptive-learning-plan", response_model=AdaptiveLearningPlanResponse)
def get_adaptive_learning_plan_endpoint(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    """Fresh, data-driven recommendations rebuilt after each saved assessment."""
    return get_adaptive_learning_plan(db, learner_id)

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
    topic_type: Optional[str] = Query(
        None, description="Restrict to 'letter' or 'motion_sign'; omit for the platform-wide mixed queue."
    ),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    return get_recommendations(db, learner_id, topic_type=topic_type)

@router.get("/{learner_id}/learning-plan", response_model=LearningPlanResponse)
def get_learner_learning_plan(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    return generate_learning_plan(db, learner_id)

@router.get("/{learner_id}/confusion-pairs", response_model=ConfusionPairsResponse)
def get_learner_confusion_pairs(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    return get_confusion_pairs(db, learner_id)

@router.get("/{learner_id}/progress", response_model=LearnerProgressResponse)
def get_learner_progress_endpoint(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    """Streak, achievements, recent activity, and performance forecast — all derived from real attempt history."""
    analytics = get_learner_analytics(db, learner_id)
    return get_learner_progress(db, learner_id, analytics)

@router.get("/{learner_id}/courses", response_model=CourseCatalogResponse)
def get_learner_courses(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    """Minimal course catalog with real progress on the one course that has progress to show (alphabet practice)."""
    analytics = get_learner_analytics(db, learner_id)
    return CourseCatalogResponse(courses=get_course_catalog(analytics, db, learner_id))

@router.get("/{learner_id}/feedback", response_model=LearnerFeedbackResponse)
def get_learner_feedback_endpoint(
    learner_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_self_or_staff),
):
    """Automated, skill-tiered feedback covering errors, performance, and areas for improvement — rebuilt fresh every call."""
    return get_learner_feedback(db, learner_id)
