"""
Read/write access to leads for the dashboard.

Reuses agent.session_store (the same module the orchestrator uses) for
per-lead reads/writes, so lead state stays single-sourced from the `leads`
table. list_leads() is the one place this module talks to agent.db
directly, since session_store has no "list all lead ids" accessor beyond
load_all_sessions() (which also loads full history/tour/recs for every
lead - wasteful for a table listing). This is a read-only presentation
query, not new business logic.
"""
from typing import List, Optional

from agent import db
from agent import session_store
from agent import booking_store
from agent.schema import LeadRequirement


def _status_for(session: dict, bookings: list) -> str:
    if any(b["status"] == "confirmed" for b in bookings):
        return "booked"
    tour = session.get("tour")
    if tour and tour.get("status") in ("proposed", "confirmed", "reminded"):
        return "tour_scheduled"
    if tour and tour.get("status") == "no_show":
        return "no_show"
    history = session.get("history") or []
    if not history:
        return "new"
    if history[-1]["direction"] == "outbound":
        return "awaiting_reply"
    return "active"


def list_leads() -> List[dict]:
    conn = db.get_connection()
    rows = conn.execute(
        "SELECT lead_id, contact_name, company_name, location, workspace_type, "
        "team_size, budget_per_seat, move_in_timeline, channel, tier, updated_at "
        "FROM leads ORDER BY updated_at DESC"
    ).fetchall()
    conn.close()

    items = []
    for row in rows:
        lead_id = row["lead_id"]
        bookings = booking_store.bookings_for_lead(lead_id)
        session = session_store.get_session(lead_id)
        items.append({
            "lead_id": lead_id,
            "contact_name": row["contact_name"],
            "company_name": row["company_name"],
            "location": row["location"],
            "workspace_type": row["workspace_type"],
            "team_size": row["team_size"],
            "budget_per_seat": row["budget_per_seat"],
            "move_in_timeline": row["move_in_timeline"],
            "channel": row["channel"],
            "tier": row["tier"],
            "status": _status_for(session, bookings),
            "last_activity": row["updated_at"],
        })
    return items


def lead_exists(lead_id: str) -> bool:
    conn = db.get_connection()
    row = conn.execute("SELECT 1 FROM leads WHERE lead_id = ?", (lead_id,)).fetchone()
    conn.close()
    return bool(row)


def get_lead_detail(lead_id: str) -> Optional[dict]:
    if not lead_exists(lead_id):
        return None
    session = session_store.get_session(lead_id)
    bookings = booking_store.bookings_for_lead(lead_id)
    return {
        "lead_id": lead_id,
        "requirement": session["requirement"],
        "tier": session["tier"],
        "history": session["history"],
        "last_recommendations": session["last_recommendations"],
        "tour": session["tour"],
        "bookings": bookings,
    }


def create_lead(payload: dict) -> dict:
    """Creates/updates a lead directly (operator-entered, not via chat free
    text). Reuses session_store.merge_requirement so it goes through the
    exact same persistence path a chat-extracted lead would."""
    lead_id = payload.get("lead_id") or f"manual-{db.now_iso().replace(':', '').replace('.', '')}"
    lead = LeadRequirement(
        lead_id=lead_id,
        channel=payload.get("channel") or "chat",
        contact_name=payload.get("contact_name"),
        company_name=payload.get("company_name"),
        location=payload.get("location"),
        team_size=payload.get("team_size"),
        workspace_type=payload.get("workspace_type"),
        budget_per_seat=payload.get("budget_per_seat"),
        move_in_timeline=payload.get("move_in_timeline"),
        requested_date=payload.get("requested_date"),
        requested_time=payload.get("requested_time"),
        raw_text=payload.get("raw_text") or "",
    )
    merged = session_store.merge_requirement(lead_id, lead)
    return get_lead_detail(merged.lead_id)


def update_lead(lead_id: str, payload: dict) -> Optional[dict]:
    if not lead_exists(lead_id):
        return None
    fields = {k: v for k, v in payload.items() if v is not None}
    if not fields:
        return get_lead_detail(lead_id)
    lead = LeadRequirement(lead_id=lead_id, raw_text="", **fields)
    session_store.merge_requirement(lead_id, lead)
    return get_lead_detail(lead_id)
