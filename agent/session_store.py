"""
Conversation memory: keyed by lead_id, persists across multiple inbound
messages from the same lead.

Without this, every message is parsed as if it were the first thing the
lead ever said - a reply of "Bangalore, 8k budget" to the agent's own
clarifying question would be treated as a brand-new, mostly-empty lead.

Phase 3: this is now backed by db.py's `leads` / `conversation_history` /
`lead_recommendations_cache` / `tours` tables instead of a JSON file. Every
public function keeps the same name and signature as the Phase 1/2 version -
orchestrator.py, tour.py, and followups.py didn't need to change at all.
"""
import json
from typing import Optional

from agent.schema import LeadRequirement
from agent import db

_FIELDS = [
    "lead_id", "channel", "company_name", "contact_name", "location",
    "team_size", "workspace_type", "budget_per_seat", "move_in_timeline",
    "requested_date", "requested_time", "raw_text", "extraction_notes",
]


def _lead_row_to_dict(row) -> dict:
    return {
        "lead_id": row["lead_id"], "channel": row["channel"],
        "company_name": row["company_name"], "contact_name": row["contact_name"],
        "location": row["location"], "team_size": row["team_size"],
        "workspace_type": row["workspace_type"], "budget_per_seat": row["budget_per_seat"],
        "move_in_timeline": row["move_in_timeline"], "requested_date": row["requested_date"],
        "requested_time": row["requested_time"], "raw_text": row["raw_text"],
        "extraction_notes": json.loads(row["extraction_notes"] or "[]"),
    }


def _ensure_lead_row(conn, lead_id: str) -> None:
    exists = conn.execute("SELECT 1 FROM leads WHERE lead_id = ?", (lead_id,)).fetchone()
    if not exists:
        now = db.now_iso()
        conn.execute(
            "INSERT INTO leads (lead_id, extraction_notes, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (lead_id, "[]", now, now),
        )


def ensure_lead(lead_id: str) -> None:
    """Public wrapper around _ensure_lead_row for callers outside this module
    (e.g. bookings_service) that need a minimal lead row to exist before an
    FK-dependent insert, without pulling in the full get_session() read.
    Idempotent - safe to call even if the lead already exists."""
    conn = db.get_connection()
    _ensure_lead_row(conn, lead_id)
    conn.commit()
    conn.close()


def get_session(lead_id: str) -> dict:
    """Returns the same shape as Phase 1/2's session dict, assembled from
    the DB: requirement, conversation history, last recommendations shown,
    any pending tour, and the last computed qualification tier."""
    conn = db.get_connection()
    _ensure_lead_row(conn, lead_id)
    conn.commit()

    lead_row = conn.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,)).fetchone()
    requirement = _lead_row_to_dict(lead_row)
    tier = lead_row["tier"]

    history_rows = conn.execute(
        "SELECT channel, direction, text, timestamp FROM conversation_history "
        "WHERE lead_id = ? ORDER BY id", (lead_id,),
    ).fetchall()
    history = [dict(r) for r in history_rows]

    rec_row = conn.execute(
        "SELECT workspaces_json FROM lead_recommendations_cache WHERE lead_id = ?", (lead_id,),
    ).fetchone()
    last_recommendations = json.loads(rec_row["workspaces_json"]) if rec_row else []

    tour_row = conn.execute("SELECT * FROM tours WHERE lead_id = ?", (lead_id,)).fetchone()
    tour = dict(tour_row) if tour_row else None
    if tour:
        tour["reminder_sent"] = bool(tour["reminder_sent"])

    conn.close()
    return {
        "lead_id": lead_id, "requirement": requirement, "history": history,
        "last_recommendations": last_recommendations, "tour": tour, "tier": tier,
    }


def merge_requirement(lead_id: str, new_lead: LeadRequirement) -> LeadRequirement:
    """
    Merges a freshly-extracted LeadRequirement into whatever this lead has
    already told the agent. New non-null values fill gaps or update fields
    the lead is re-specifying; nothing already known is silently dropped
    just because a later message didn't repeat it.
    """
    conn = db.get_connection()
    _ensure_lead_row(conn, lead_id)
    conn.commit()

    stored_row = conn.execute("SELECT * FROM leads WHERE lead_id = ?", (lead_id,)).fetchone()
    stored = _lead_row_to_dict(stored_row)

    merged = LeadRequirement(**{f: stored.get(f) for f in _FIELDS})
    merged.lead_id = lead_id

    new_dict = new_lead.to_dict()
    for f in _FIELDS:
        if f in ("lead_id", "raw_text", "extraction_notes"):
            continue
        val = new_dict.get(f)
        if val not in (None, ""):
            setattr(merged, f, val)

    merged.raw_text = new_lead.raw_text  # always keep the latest verbatim message
    merged.channel = new_lead.channel or merged.channel
    merged.extraction_notes = (stored.get("extraction_notes") or []) + new_lead.extraction_notes

    conn.execute(
        """UPDATE leads SET channel=?, company_name=?, contact_name=?, location=?, team_size=?,
           workspace_type=?, budget_per_seat=?, move_in_timeline=?, requested_date=?,
           requested_time=?, raw_text=?, extraction_notes=?, updated_at=? WHERE lead_id=?""",
        (merged.channel, merged.company_name, merged.contact_name, merged.location, merged.team_size,
         merged.workspace_type, merged.budget_per_seat, merged.move_in_timeline, merged.requested_date,
         merged.requested_time, merged.raw_text, json.dumps(merged.extraction_notes), db.now_iso(), lead_id),
    )
    conn.commit()
    conn.close()
    return merged


def append_history(lead_id: str, channel: Optional[str], direction: str, text: str, timestamp: str) -> None:
    conn = db.get_connection()
    _ensure_lead_row(conn, lead_id)
    conn.execute(
        "INSERT INTO conversation_history (lead_id, channel, direction, text, timestamp) VALUES (?, ?, ?, ?, ?)",
        (lead_id, channel, direction, text, timestamp),
    )
    conn.commit()
    conn.close()


def set_last_recommendations(lead_id: str, workspaces: list) -> None:
    conn = db.get_connection()
    _ensure_lead_row(conn, lead_id)
    conn.execute(
        """INSERT INTO lead_recommendations_cache (lead_id, workspaces_json) VALUES (?, ?)
           ON CONFLICT(lead_id) DO UPDATE SET workspaces_json = excluded.workspaces_json""",
        (lead_id, json.dumps(workspaces)),
    )
    conn.commit()
    conn.close()


def get_last_recommendations(lead_id: str) -> list:
    return get_session(lead_id).get("last_recommendations") or []


def get_full_history(lead_id: str) -> list:
    return get_session(lead_id).get("history") or []


def set_tour(lead_id: str, tour: Optional[dict]) -> None:
    conn = db.get_connection()
    _ensure_lead_row(conn, lead_id)
    if tour is None:
        conn.execute("DELETE FROM tours WHERE lead_id = ?", (lead_id,))
    else:
        conn.execute(
            """INSERT INTO tours (lead_id, workspace_id, workspace_name, proposed_time, status, reminder_sent)
               VALUES (?, ?, ?, ?, ?, ?)
               ON CONFLICT(lead_id) DO UPDATE SET workspace_id=excluded.workspace_id,
                   workspace_name=excluded.workspace_name, proposed_time=excluded.proposed_time,
                   status=excluded.status, reminder_sent=excluded.reminder_sent""",
            (lead_id, tour["workspace_id"], tour["workspace_name"], tour["proposed_time"],
             tour["status"], int(tour.get("reminder_sent", False))),
        )
    conn.commit()
    conn.close()


def get_tour(lead_id: str) -> Optional[dict]:
    return get_session(lead_id).get("tour")


def set_last_tier(lead_id: str, tier: str) -> None:
    """Tracks each lead's most recent qualification tier, so a follow-up
    sweep (agent/followups.py) can decide whether a stale warm/cold lead is
    worth nudging, without recomputing qualification from scratch."""
    conn = db.get_connection()
    _ensure_lead_row(conn, lead_id)
    conn.execute("UPDATE leads SET tier = ?, updated_at = ? WHERE lead_id = ?", (tier, db.now_iso(), lead_id))
    conn.commit()
    conn.close()


def get_last_tier(lead_id: str) -> Optional[str]:
    return get_session(lead_id).get("tier")


def load_all_sessions() -> dict:
    """Public accessor for scheduler-style jobs (e.g. tour/follow-up sweeps)."""
    conn = db.get_connection()
    lead_ids = [r["lead_id"] for r in conn.execute("SELECT lead_id FROM leads").fetchall()]
    conn.close()
    return {lid: get_session(lid) for lid in lead_ids}
