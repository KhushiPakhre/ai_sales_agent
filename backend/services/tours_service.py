"""
Tour CRUD for the operator dashboard/API.

The `tours` table (agent/db.py) keys one active tour per lead_id, so a
"tour_id" in this API is the lead_id - there's no separate tour ID in the
existing schema, and introducing one would mean changing agent/db.py for a
dashboard-only convenience. Reads/writes go through session_store.set_tour /
get_tour, the same functions agent/tour.py uses, so a tour created here and
one proposed automatically by the chat agent live in exactly one place.
"""
from typing import List, Optional

from agent import db
from agent import session_store
from agent.recommender import get_workspace


def list_tours() -> List[dict]:
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM tours ORDER BY proposed_time DESC").fetchall()
    conn.close()
    tours = []
    for r in rows:
        t = dict(r)
        t["reminder_sent"] = bool(t["reminder_sent"])
        tours.append(t)
    return tours


def get_tour(lead_id: str) -> Optional[dict]:
    return session_store.get_tour(lead_id)


def create_tour(payload: dict) -> dict:
    ws = get_workspace(payload["workspace_id"])
    if not ws:
        raise ValueError(f"No workspace with id {payload['workspace_id']}")
    tour = {
        "lead_id": payload["lead_id"],
        "workspace_id": ws["id"],
        "workspace_name": ws["name"],
        "proposed_time": payload["proposed_time"],
        "status": payload.get("status", "proposed"),
        "reminder_sent": False,
    }
    session_store.set_tour(payload["lead_id"], tour)
    return tour


def update_tour(lead_id: str, payload: dict) -> Optional[dict]:
    existing = session_store.get_tour(lead_id)
    if not existing:
        return None
    fields = {k: v for k, v in payload.items() if v is not None}
    merged = {**existing, **fields}
    session_store.set_tour(lead_id, merged)
    return merged
