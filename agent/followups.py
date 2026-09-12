"""
Follow-ups for leads that went quiet - distinct from tour.py's reminder/
no-show handling, which only covers leads with a scheduled tour. A warm or
cold lead who got recommendations but never replied has no tour to remind
about, and previously had no follow-up mechanism at all.

Like tour.check_reminders, this is written to be called by a scheduler on
a regular cadence (e.g. daily), not to run itself on a timer.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional

from agent import session_store
from agent import booking_store

STALE_AFTER_HOURS = {"warm": 48, "cold": 120}


def check_stale_leads(now: Optional[datetime] = None) -> list:
    """
    Returns leads whose last message was outbound (the lead never replied)
    and who've gone quiet longer than their tier's threshold. Hot leads are
    excluded - they either already got a tour/instant booking, or are
    urgent enough that a human should already be on it, not queued for an
    automated nudge. Leads with an active confirmed booking are excluded
    too - they got what they came for; nudging them to "still looking?"
    would be tone-deaf, not helpful.
    """
    now = now or datetime.now(timezone.utc)
    sessions = session_store.load_all_sessions()
    due = []
    for lead_id, session in sessions.items():
        history = session.get("history") or []
        if not history or history[-1]["direction"] != "outbound":
            continue
        tier = session.get("tier")
        threshold_hours = STALE_AFTER_HOURS.get(tier)
        if not threshold_hours:
            continue
        if any(b["status"] == "confirmed" for b in booking_store.bookings_for_lead(lead_id)):
            continue  # already got what they came for
        if session.get("tour") and session["tour"].get("status") in ("proposed", "confirmed", "reminded"):
            continue  # tour.py owns this lead's follow-up cadence while a tour is pending
        last_time = datetime.fromisoformat(history[-1]["timestamp"])
        if (now - last_time) >= timedelta(hours=threshold_hours):
            due.append({"lead_id": lead_id, "tier": tier, "last_outbound": history[-1]["timestamp"]})
    return due


def draft_followup(lead_id: str) -> Optional[str]:
    session = session_store.get_session(lead_id)
    requirement = session.get("requirement") or {}
    name = requirement.get("contact_name") or "there"
    tier = session.get("tier")

    if tier == "warm":
        return (
            f"Hi {name}, just checking back in - still looking for a workspace? Happy to "
            f"share updated options or availability whenever you're ready."
        )
    if tier == "cold":
        return (
            f"Hi {name}, no rush at all - whenever your plans firm up, I'm here to help "
            f"you find the right workspace."
        )
    return None
