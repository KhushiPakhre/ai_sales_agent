"""Wraps agent.availability (already DB-backed) for the dashboard/API."""
from datetime import date as date_cls
from typing import Optional

from agent import availability
from agent.recommender import get_workspace


def check_availability(workspace_id: str, date_str: Optional[str] = None) -> Optional[dict]:
    ws = get_workspace(workspace_id)
    if not ws:
        return None
    check_date = date_str or date_cls.today().isoformat()
    daily_capacity = ws.get("daily_capacity") or 5
    slots_remaining = availability.get_available_slots(workspace_id, check_date, daily_capacity)
    return {
        "workspace_id": workspace_id,
        "date": check_date,
        "daily_capacity": daily_capacity,
        "slots_remaining": slots_remaining,
        "is_available": slots_remaining > 0,
    }
