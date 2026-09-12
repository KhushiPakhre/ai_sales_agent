from typing import Optional
from pydantic import BaseModel


class TourOut(BaseModel):
    lead_id: str
    workspace_id: str
    workspace_name: str
    proposed_time: str
    status: str
    reminder_sent: bool


class TourCreate(BaseModel):
    lead_id: str
    workspace_id: str
    proposed_time: str  # ISO 8601
    status: str = "proposed"


class TourUpdate(BaseModel):
    status: Optional[str] = None  # proposed | confirmed | reminded | no_show | completed
    proposed_time: Optional[str] = None
    reminder_sent: Optional[bool] = None
