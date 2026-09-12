from typing import List, Optional
from pydantic import BaseModel, Field


class WorkspaceOut(BaseModel):
    id: str
    name: str
    city: str
    workspace_type: str
    capacity_min: int
    capacity_max: int
    price_per_seat_inr: int
    amenities: List[str]
    available_from: str
    rating: float
    daily_capacity: Optional[int] = None


class WorkspaceCreate(BaseModel):
    id: Optional[str] = None
    name: str
    city: str
    workspace_type: str
    capacity_min: int
    capacity_max: int
    price_per_seat_inr: int
    amenities: List[str] = Field(default_factory=list)
    available_from: str = "immediate"
    rating: float = 4.0
    daily_capacity: Optional[int] = None


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    workspace_type: Optional[str] = None
    capacity_min: Optional[int] = None
    capacity_max: Optional[int] = None
    price_per_seat_inr: Optional[int] = None
    amenities: Optional[List[str]] = None
    available_from: Optional[str] = None
    rating: Optional[float] = None
    daily_capacity: Optional[int] = None


class AvailabilityOut(BaseModel):
    workspace_id: str
    date: str
    daily_capacity: int
    slots_remaining: int
    is_available: bool
