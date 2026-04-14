from pydantic import BaseModel

from .enums import DecisionType


class ReviewActionRequest(BaseModel):
    reviewer_id: str
    notes: str
    decision: DecisionType | None = None
    reviewer_queue: str | None = None