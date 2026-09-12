from fastapi import APIRouter, HTTPException
import logging

from backend.schemas.chat import ChatMessageIn
from backend.services import chat_service

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger("qdesq.chat")


@router.post("/message")
def post_message(payload: ChatMessageIn):
    try:
        return chat_service.send_message(payload.lead_id, payload.channel, payload.message)
    except Exception:
        # Never leak a stack trace to the chat UI - log server-side, return
        # a generic error the frontend can show with a retry action.
        logger.exception("Chat message processing failed for lead_id=%s", payload.lead_id)
        raise HTTPException(status_code=500, detail="Something went wrong processing that message. Please try again.")


@router.get("/{lead_id}/history")
def get_history(lead_id: str):
    return {"lead_id": lead_id, "history": chat_service.get_history(lead_id)}
