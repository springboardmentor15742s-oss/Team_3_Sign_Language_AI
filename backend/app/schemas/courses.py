from typing import Optional

from pydantic import BaseModel


class CourseItem(BaseModel):
    id: str
    title: str
    category: str
    description: str
    route: Optional[str] = None
    built: bool
    tracks_progress: bool
    # Null whenever progress isn't tracked or isn't computable — never a
    # placeholder number for a course that doesn't exist yet.
    progress_percent: Optional[float] = None
    item_count: Optional[int] = None
    locked_reason: Optional[str] = None


class CourseCatalogResponse(BaseModel):
    courses: list[CourseItem]
