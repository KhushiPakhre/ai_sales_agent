"""
Chat endpoint logic - a thin adapter over agent.orchestrator.run_agent.

The frontend doesn't need every internal field the orchestrator returns
(qualification.reasons, extraction_notes, etc.) - this reshapes the result
into the smaller contract described in the spec (message/intent/
qualification/recommendations/action/booking/tour/handoff), without
changing anything about how the agent itself decides or drafts.
"""
from agent.orchestrator import run_agent
from agent import session_store


def send_message(lead_id: str, channel: str, message: str) -> dict:
    result = run_agent(message, lead_id=lead_id, channel=channel)
    next_action = result["next_action"]

    tour = session_store.get_tour(lead_id) if next_action.get("assign_to_human") else None

    return {
        "lead_id": result["lead_id"],
        "message": next_action["message"],
        "intent": result.get("intent"),
        "qualification": result.get("qualification"),
        "recommendations": result.get("recommendations", []),
        "action": next_action["action"],
        "booking": next_action.get("booking"),
        "tour": tour,
        "handoff": result.get("handoff"),
    }


def get_history(lead_id: str) -> list:
    return session_store.get_full_history(lead_id)
