from typing import List

from pydantic import BaseModel

class ConfusionPair(BaseModel):
    target_letter: str
    predicted_letter: str
    count: int

class ConfusionPairsResponse(BaseModel):
    learner_id: str
    pairs: List[ConfusionPair]
