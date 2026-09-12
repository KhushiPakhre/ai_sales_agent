from typing import Optional
from pydantic import BaseModel


class BookingOut(BaseModel):
    booking_id: str
    lead_id: str
    workspace_id: str
    workspace_name: str
    workspace_type: str
    city: str
    date: str
    time: Optional[str] = None
    seats: int
    status: str
    created_at: str


class BookingCreate(BaseModel):
    lead_id: str
    workspace_id: str
    date: str
    time: Optional[str] = None
    seats: int = 1


class BookingUpdate(BaseModel):
    status: str  # confirmed | cancelled | no_show | completed
