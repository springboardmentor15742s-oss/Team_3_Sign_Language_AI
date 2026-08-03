from fastapi import APIRouter
from app.services.dataset_service import get_dataset_summary

router = APIRouter(prefix="/dataset", tags=["ASL Dataset"])


@router.get("/summary")
def dataset_summary():
    """Return ASL dataset status, available classes, and image counts."""
    return get_dataset_summary()
