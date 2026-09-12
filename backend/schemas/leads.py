from typing import List, Optional
from pydantic import BaseModel, Field


class LeadRequirementOut(BaseModel):
    lead_id: Optional[str] = None
    channel: Optional[str] = None
    company_name: Optional[str] = None
    contact_name: Optional[str] = None
    location: Optional[str] = None
    team_size: Optional[int] = None
    workspace_type: Optional[str] = None
    budget_per_seat: Optional[int] = None
    move_in_timeline: Optional[str] = None
    requested_date: Optional[str] = None
    requested_time: Optional[str] = None
    raw_text: Optional[str] = None
    extraction_notes: List[str] = Field(default_factory=list)


class LeadListItem(BaseModel):
    lead_id: str
    contact_name: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    workspace_type: Optional[str] = None
    team_size: Optional[int] = None
    budget_per_seat: Optional[int] = None
    move_in_timeline: Optional[str] = None
    channel: Optional[str] = None
    tier: Optional[str] = None
    status: str
    last_activity: Optional[str] = None


class LeadDetail(BaseModel):
    lead_id: str
    requirement: LeadRequirementOut
    tier: Optional[str] = None
    history: list
    last_recommendations: list
    tour: Optional[dict] = None
    bookings: list
    handoff: Optional[dict] = None


class LeadCreate(BaseModel):
    """Create a lead directly (e.g. from a web form), bypassing free-text extraction."""
    lead_id: Optional[str] = None
    channel: Optional[str] = "chat"
    contact_name: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    team_size: Optional[int] = None
    workspace_type: Optional[str] = None
    budget_per_seat: Optional[int] = None
    move_in_timeline: Optional[str] = None
    requested_date: Optional[str] = None
    requested_time: Optional[str] = None
    raw_text: Optional[str] = None


class LeadUpdate(BaseModel):
    contact_name: Optional[str] = None
    company_name: Optional[str] = None
    location: Optional[str] = None
    team_size: Optional[int] = None
    workspace_type: Optional[str] = None
    budget_per_seat: Optional[int] = None
    move_in_timeline: Optional[str] = None
    requested_date: Optional[str] = None
    requested_time: Optional[str] = None
