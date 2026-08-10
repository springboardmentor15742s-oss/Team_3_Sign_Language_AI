from typing import List

from pydantic import BaseModel

class RecommendationItem(BaseModel):
    letter: str
    reason: str

class RecommendationsResponse(BaseModel):
    learner_id: str
    recommendations: List[RecommendationItem]
