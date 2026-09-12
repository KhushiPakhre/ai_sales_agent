from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessageIn(BaseModel):
    lead_id: str = Field(..., description="Stable identifier for this lead/session, e.g. 'chat:session-123'")
    channel: str = Field(default="chat", description="whatsapp | email | chat")
    message: str = Field(..., min_length=1)


class ChatMessageOut(BaseModel):
    lead_id: str
    message: str
    intent: Optional[str] = None
    qualification: Optional[dict] = None
    recommendations: List[dict] = Field(default_factory=list)
    action: str
    booking: Optional[dict] = None
    tour: Optional[dict] = None
    handoff: Optional[dict] = None


class ChatHistoryTurn(BaseModel):
    channel: Optional[str] = None
    direction: str
    text: str
    timestamp: str


class ChatHistoryOut(BaseModel):
    lead_id: str
    history: List[ChatHistoryTurn]
