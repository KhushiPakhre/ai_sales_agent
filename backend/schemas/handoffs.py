from typing import List, Optional
from pydantic import BaseModel


class HandoffOut(BaseModel):
    lead_id: str
    contact_name: Optional[str] = None
    company_name: Optional[str] = None
    urgency: str
    reason: str
    summary: str
    suggested_next_step: str
    action_name: str
    timestamp: str
    conversation_history: List[dict] = []


class AnalyticsOut(BaseModel):
    total_leads: int
    hot_leads: int
    warm_leads: int
    cold_leads: int
    total_bookings: int
    total_tours: int
    pending_handoffs: int
    conversion_rate: float
    tour_show_rate: Optional[float] = None
    workspace_utilization: List[dict] = []
