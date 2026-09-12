"""Matches a lead's requirement against the workspace inventory (DB-backed, Phase 3)."""
import json
from dataclasses import dataclass
from datetime import date
from typing import List, Optional

from agent.schema import LeadRequirement
from agent.amenities import requested_amenities
from agent import availability
from agent import db

# available_from values below this many days out count as "soon enough" for
# an immediate-timeline lead, since "immediate" inventory entries themselves
# use the literal string "immediate" rather than a day count.
IMMEDIATE_AVAILABILITY_TOLERANCE_DAYS = 3


@dataclass
class RecommendationResult:
    workspace: dict
    match_score: int
    match_reasons: List[str]


def _row_to_dict(row) -> dict:
    return {
        "id": row["id"], "name": row["name"], "city": row["city"],
        "workspace_type": row["workspace_type"], "capacity_min": row["capacity_min"],
        "capacity_max": row["capacity_max"], "price_per_seat_inr": row["price_per_seat_inr"],
        "amenities": json.loads(row["amenities"]), "available_from": row["available_from"],
        "rating": row["rating"], "daily_capacity": row["daily_capacity"],
    }


def _load_workspaces() -> List[dict]:
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM workspaces").fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def _availability_days(available_from: str) -> int:
    if available_from == "immediate":
        return 0
    try:
        return int(available_from.split()[0])
    except (ValueError, IndexError):
        return 9999  # unparseable -> treat as far out rather than crash


def recommend_workspaces(lead: LeadRequirement, top_n: int = 3) -> List[RecommendationResult]:
    workspaces = _load_workspaces()
    results = []
    wanted_amenities = requested_amenities(lead.raw_text)

    for ws in workspaces:
        score = 0
        reasons = []

        # For instant-book types, check the actual date the lead wants -
        # a workspace fully booked tomorrow may well be free today.
        if ws["workspace_type"] in ("day_pass", "meeting_room"):
            check_date = lead.requested_date or date.today().isoformat()
            if availability.get_available_slots(ws["id"], check_date, ws.get("daily_capacity") or 5) <= 0:
                continue

        if lead.location and ws["city"].lower() == lead.location.lower():
            score += 40
            reasons.append("city match")
        elif lead.location:
            continue  # hard filter: don't recommend the wrong city

        if lead.team_size:
            if ws["capacity_min"] <= lead.team_size <= ws["capacity_max"]:
                score += 25
                reasons.append("fits team size")
            else:
                continue  # hard filter: capacity must be able to hold the team

        if lead.workspace_type and ws["workspace_type"] == lead.workspace_type:
            score += 20
            reasons.append("workspace type match")
        elif lead.workspace_type:
            score += 5  # soft penalty rather than exclusion - still show as an option

        if lead.budget_per_seat:
            if ws["price_per_seat_inr"] <= lead.budget_per_seat:
                score += 15
                reasons.append("within budget")
            elif ws["price_per_seat_inr"] <= lead.budget_per_seat * 1.15:
                score += 5
                reasons.append("slightly over budget (within 15%)")
            else:
                continue  # hard filter: too far over budget

        # Availability vs. move-in timeline. A lead needing an immediate
        # move-in shouldn't be shown a workspace that's 45-60 days out -
        # this was previously ignored entirely.
        days_out = _availability_days(ws["available_from"])
        if lead.move_in_timeline == "immediate":
            if days_out > IMMEDIATE_AVAILABILITY_TOLERANCE_DAYS:
                continue  # hard filter: not actually available soon enough
            reasons.append("available in time")
        elif lead.move_in_timeline:
            # "n days/weeks/months" - soft-score how close availability is
            # to the lead's own timeline instead of hard-excluding, since a
            # workspace ready a bit sooner than needed is still fine.
            parts = lead.move_in_timeline.split()
            if len(parts) == 2 and parts[0].isdigit():
                n, unit = int(parts[0]), parts[1]
                lead_days = n * {"day": 1, "days": 1, "week": 7, "weeks": 7,
                                 "month": 30, "months": 30}.get(unit, 30)
                if days_out <= lead_days:
                    score += 5
                    reasons.append("available in time")

        # Soft amenity match against anything the lead's message explicitly asked for.
        if wanted_amenities:
            ws_amenities = [a.lower() for a in ws.get("amenities", [])]
            matched = [a for a in wanted_amenities if any(a in wa for wa in ws_amenities)]
            if matched:
                score += 5 * len(matched)
                reasons.append(f"has requested amenities ({', '.join(matched)})")

        score += round(ws["rating"] * 2)  # small tiebreaker for quality

        results.append(RecommendationResult(workspace=ws, match_score=score, match_reasons=reasons))

    results.sort(key=lambda r: r.match_score, reverse=True)
    return results[:top_n]


def _get_workspace_row(workspace_id: str) -> Optional[dict]:
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM workspaces WHERE id = ?", (workspace_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def book(workspace_id: str, date_str: str, seats_needed: int = 1) -> bool:
    """
    Actually holds a slot for an instant-book workspace (day pass / meeting
    room) on a specific date, via the shared calendar. Returns False if
    there isn't enough capacity left that day, so the caller can fall back
    instead of confirming a booking that doesn't exist.
    """
    ws = _get_workspace_row(workspace_id)
    if not ws:
        return False
    return availability.reserve(workspace_id, date_str, seats_needed, ws.get("daily_capacity") or 5)


def release(workspace_id: str, date_str: str, seats: int = 1) -> None:
    """Frees seats back to a date's availability - e.g. on cancellation or no-show."""
    ws = _get_workspace_row(workspace_id)
    if ws:
        availability.release(workspace_id, date_str, seats, ws.get("daily_capacity") or 5)


def get_workspace(workspace_id: str) -> Optional[dict]:
    return _get_workspace_row(workspace_id)
