from typing import List, Literal

from pydantic import BaseModel

class RecommendationItem(BaseModel):
    topic: str
    topic_type: Literal["letter", "motion_sign"]
    reason: str

class RecommendationsResponse(BaseModel):
    learner_id: str
    recommendations: List[RecommendationItem]
