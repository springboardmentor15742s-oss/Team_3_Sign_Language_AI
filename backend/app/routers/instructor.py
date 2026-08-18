from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.instructor import LearnerRosterResponse
from app.services.auth_dependency import require_role
from app.services.instructor_service import get_learner_roster

router = APIRouter(prefix="/api/instructor", tags=["Instructor"])

@router.get("/learners", response_model=LearnerRosterResponse)
def list_learners(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("instructor", "admin")),
):
    return {"learners": get_learner_roster(db)}
