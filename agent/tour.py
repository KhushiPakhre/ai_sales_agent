"""
Tour scheduling, reminders, and no-show follow-up - explicitly listed on
the AI side of Smart Handoff ("Tour reminders & no-show follow-ups"), but
previously nonexistent: the old code only ever drafted a message *suggesting*
a call, with no record of a tour, no reminder trigger, and no no-show path.

Reminders/no-shows depend on real wall-clock time passing, which a single
request/response pipeline can't drive on its own - `check_reminders` and
`mark_no_show` are written to be called by a scheduler (cron/worker) once
this is deployed, and are exercised directly in main.py's demo to show the
behavior without waiting for real time to pass.
"""
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Optional

from agent.schema import LeadRequirement
from agent import session_store

# How far out a first tour slot is proposed, by urgency tier.
PROPOSAL_OFFSET_HOURS = {"hot": 24, "warm": 72, "cold": 168}


@dataclass
class Tour:
    lead_id: str
    workspace_id: str
    workspace_name: str
    proposed_time: str  # ISO 8601
    status: str  # "proposed" | "confirmed" | "reminded" | "no_show" | "completed"
    reminder_sent: bool = False


def propose_tour(lead: LeadRequirement, workspace: dict, tier: str, now: Optional[datetime] = None) -> Tour:
    now = now or datetime.now(timezone.utc)
    if lead.requested_date:
        # Lead already told us which day works for them - honor it instead
        # of guessing from tier alone. Default to a reasonable business
        # hour if they didn't also give a time.
        hour, minute = 11, 0
        if lead.requested_time:
            hour, minute = (int(x) for x in lead.requested_time.split(":"))
        proposed_time = datetime.fromisoformat(f"{lead.requested_date}T00:00:00+00:00").replace(
            hour=hour, minute=minute
        ).isoformat()
    else:
        offset = PROPOSAL_OFFSET_HOURS.get(tier, 72)
        proposed_time = (now + timedelta(hours=offset)).isoformat()

    tour = Tour(
        lead_id=lead.lead_id,
        workspace_id=workspace["id"],
        workspace_name=workspace["name"],
        proposed_time=proposed_time,
        status="proposed",
    )
    session_store.set_tour(lead.lead_id, asdict(tour))
    return tour


def check_reminders(now: Optional[datetime] = None, hours_before: int = 24) -> list:
    """
    Called by a scheduler on a regular cadence. Returns tours that are
    within `hours_before` of their proposed time and haven't been reminded
    yet, marking them as reminded so this doesn't fire twice.
    """
    now = now or datetime.now(timezone.utc)
    sessions = session_store.load_all_sessions()
    due = []
    for lead_id, session in sessions.items():
        tour = session.get("tour")
        if not tour or tour.get("reminder_sent") or tour.get("status") not in ("proposed", "confirmed"):
            continue
        proposed = datetime.fromisoformat(tour["proposed_time"])
        if proposed - timedelta(hours=hours_before) <= now < proposed:
            tour["reminder_sent"] = True
            tour["status"] = "reminded"
            session_store.set_tour(lead_id, tour)
            due.append({"lead_id": lead_id, "tour": tour})
    return due


def mark_no_show(lead_id: str) -> Optional[str]:
    """
    Marks a tour as a no-show and drafts a follow-up message. Returns None
    if there's no tour on file for this lead.
    """
    tour = session_store.get_tour(lead_id)
    if not tour:
        return None
    tour["status"] = "no_show"
    session_store.set_tour(lead_id, tour)
    return (
        f"Hi, we missed you at {tour['workspace_name']} for your scheduled tour. "
        f"No worries - want to pick a new time that works better?"
    )
