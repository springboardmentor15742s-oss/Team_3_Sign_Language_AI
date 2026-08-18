from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel

class AdminUserEntry(BaseModel):
    id: str
    name: str
    email: str
    role: str
    created_at: datetime
    total_attempts: Optional[int] = None  # null for non-learner roles, never 0

class AdminOverviewResponse(BaseModel):
    total_users: int
    role_counts: Dict[str, int]
    total_practice_attempts: int
    overall_accuracy_percent: Optional[float] = None
    users: List[AdminUserEntry]
