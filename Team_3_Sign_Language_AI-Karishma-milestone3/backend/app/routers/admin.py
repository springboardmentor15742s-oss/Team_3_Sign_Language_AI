from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.admin import AdminOverviewResponse
from app.services.admin_service import get_admin_overview
from app.services.auth_dependency import require_role

router = APIRouter(prefix="/api/admin", tags=["Admin"])

@router.get("/overview", response_model=AdminOverviewResponse)
def get_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role("admin")),
):
    return get_admin_overview(db)
