from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AssignmentCreate(BaseModel):
    topic: str
    topic_type: str  # letter, motion_sign, word_sign


class AssignmentCompleteRequest(BaseModel):
    completed: bool = True


class AssignmentResponse(BaseModel):
    id: str
    learner_id: str
    instructor_id: str
    instructor_name: Optional[str] = None
    topic: str
    topic_type: str
    notes: Optional[str] = None
    due_date: Optional[str] = None  # "YYYY-MM-DD"
    completed: bool = False
    completed_at: Optional[datetime] = None
    # Populated only when the instructor attached a reference photo/video.
    # reference_media_url is a ready-to-use /media/... path (already
    # combined with the stored relative path) so the frontend never has
    # to know the storage layout — see media_upload_service.
    reference_media_url: Optional[str] = None
    reference_media_type: Optional[str] = None  # image, video
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AssignmentListResponse(BaseModel):
    assignments: list[AssignmentResponse]
