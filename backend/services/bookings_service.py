"""
Booking CRUD for the operator dashboard/API - distinct from the instant-book
path inside agent/next_action.py (which fires automatically from chat for
day_pass/meeting_room leads). This lets an operator create a booking
directly (e.g. over the phone), while still going through the same
booking_store + availability machinery so both paths can never double-book
the same slot.
"""
from typing import List, Optional

from agent import booking_store, session_store
from agent.recommender import get_workspace, book, release


class BookingError(Exception):
    pass


def list_bookings() -> List[dict]:
    conn = booking_store.db.get_connection()
    rows = conn.execute("SELECT * FROM bookings ORDER BY created_at DESC").fetchall()
    conn.close()
    return [booking_store._row_to_dict(r) for r in rows]


def get_booking(booking_id: str) -> Optional[dict]:
    return booking_store.get_booking(booking_id)


def create_booking(payload: dict) -> dict:
    workspace_id = payload["workspace_id"]
    ws = get_workspace(workspace_id)
    if not ws:
        raise BookingError(f"No workspace with id {workspace_id}")

    lead_id = payload["lead_id"]
    date_str = payload["date"]
    seats = max(1, payload.get("seats") or 1)

    # The bookings table has a FK on lead_id. The operator/API-driven booking
    # flow (unlike the chat flow, where session_store already creates a lead
    # row on the first inbound message) can be the very first time this
    # lead_id is seen, so make sure a minimal lead record exists first -
    # the same upsert-a-stub-row pattern session_store already uses for
    # every other FK-dependent write (history, recommendations, tours).
    # This keeps the FK constraint intact rather than weakening it.
    session_store.ensure_lead(lead_id)

    # Duplicate-booking protection: same lead + workspace type + date already
    # has a confirmed booking - reuse the existing record instead of holding
    # a second slot for what is very likely a retried/duplicate request.
    existing = booking_store.get_active_booking(lead_id, ws["workspace_type"], date_str)
    if existing:
        return existing

    if not book(workspace_id, date_str, seats_needed=seats):
        raise BookingError("No availability for that workspace on that date/capacity.")

    try:
        record = booking_store.create_booking(lead_id, ws, date_str, payload.get("time"), seats)
    except booking_store.BookingIntegrityError as exc:
        # Slot was already reserved above - release it back rather than
        # leaking a held seat if the insert itself failed unexpectedly.
        release(workspace_id, date_str, seats)
        raise BookingError(str(exc)) from exc
    return booking_store.get_booking(record.booking_id)


def update_booking_status(booking_id: str, status: str) -> Optional[dict]:
    existing = booking_store.get_booking(booking_id)
    if not existing:
        return None
    if status in ("cancelled", "no_show") and existing["status"] == "confirmed":
        # Release the held slot back to that date's availability.
        release(existing["workspace_id"], existing["date"], existing["seats"])
    return booking_store.update_status(booking_id, status)
