"""
Handoffs read model.

There's no dedicated "handoffs" table in agent/db.py - a handoff is a
per-message decision (`next_action.assign_to_human`) that the orchestrator
already logs, in full, to crm_log.json (agent/orchestrator.py's mock CRM
mirror) every time it fires. Rather than add a new table for something the
existing code already persists, this reads that log and reshapes it -
keeping only the latest handoff-carrying entry per lead, since a lead can
be escalated more than once across separate messages and the dashboard
should show current state, not every historical escalation.

"Pending" = the lead's latest handoff-carrying entry has no confirmed
booking recorded after it - i.e. nobody has closed the loop yet. This is
computed from data that's actually on file, not fabricated.
"""
import json
import os
from typing import List, Optional

from agent.orchestrator import CRM_LOG_PATH
from agent import booking_store


def _load_log() -> list:
    if not os.path.exists(CRM_LOG_PATH):
        return []
    try:
        with open(CRM_LOG_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _latest_handoffs() -> dict:
    """lead_id -> latest crm_log entry that carries a handoff packet."""
    latest = {}
    for entry in _load_log():
        if entry.get("handoff"):
            latest[entry["lead_id"]] = entry
    return latest


def _shape(entry: dict) -> dict:
    handoff = entry["handoff"]
    lead = entry.get("lead") or {}
    return {
        "lead_id": entry["lead_id"],
        "contact_name": lead.get("contact_name"),
        "company_name": lead.get("company_name"),
        "urgency": handoff["urgency"],
        "reason": handoff["reason"],
        "summary": handoff["summary"],
        "suggested_next_step": handoff["suggested_next_step"],
        "action_name": entry["next_action"]["action"],
        "timestamp": entry["timestamp"],
        "conversation_history": entry.get("conversation_history", []),
    }


def list_handoffs(pending_only: bool = False) -> List[dict]:
    results = []
    for lead_id, entry in _latest_handoffs().items():
        is_pending = not any(
            b["status"] == "confirmed" for b in booking_store.bookings_for_lead(lead_id)
        )
        if pending_only and not is_pending:
            continue
        results.append(_shape(entry))
    results.sort(key=lambda h: h["timestamp"], reverse=True)
    return results


def get_handoff(lead_id: str) -> Optional[dict]:
    entry = _latest_handoffs().get(lead_id)
    return _shape(entry) if entry else None


def pending_count() -> int:
    return len(list_handoffs(pending_only=True))
