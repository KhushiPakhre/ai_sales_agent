"""
Persistent booking records - Phase 3: now the `bookings` table in db.py
instead of a JSON file. Same public interface as Phase 2's version, so
next_action.py and main.py didn't need to change.
"""
import sqlite3
import uuid
from dataclasses import dataclass
from typing import Optional

from agent import db


class BookingIntegrityError(Exception):
    """Raised when a booking insert violates a DB constraint (e.g. an FK to
    a lead/workspace that doesn't exist) - callers should turn this into a
    clean validation error rather than letting a raw sqlite3 exception
    surface up to an API response."""


@dataclass
class Booking:
    booking_id: str
    lead_id: str
    workspace_id: str
    workspace_name: str
    workspace_type: str
    city: str
    date: str
    time: Optional[str]
    seats: int
    status: str
    created_at: str


def _row_to_dict(row) -> dict:
    return {
        "booking_id": row["booking_id"], "lead_id": row["lead_id"],
        "workspace_id": row["workspace_id"], "workspace_name": row["workspace_name"],
        "workspace_type": row["workspace_type"], "city": row["city"],
        "date": row["date"], "time": row["time"], "seats": row["seats"],
        "status": row["status"], "created_at": row["created_at"],
    }


def create_booking(lead_id: str, workspace: dict, date_str: str, time_str: Optional[str], seats: int) -> Booking:
    booking = Booking(
        booking_id=f"QD-{workspace['id']}-{uuid.uuid4().hex[:6].upper()}",
        lead_id=lead_id,
        workspace_id=workspace["id"],
        workspace_name=workspace["name"],
        workspace_type=workspace["workspace_type"],
        city=workspace["city"],
        date=date_str,
        time=time_str,
        seats=seats,
        status="confirmed",
        created_at=db.now_iso(),
    )
    conn = db.get_connection()
    try:
        conn.execute(
            """INSERT INTO bookings
               (booking_id, lead_id, workspace_id, workspace_name, workspace_type, city, date, time, seats, status, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (booking.booking_id, booking.lead_id, booking.workspace_id, booking.workspace_name,
             booking.workspace_type, booking.city, booking.date, booking.time, booking.seats,
             booking.status, booking.created_at),
        )
        conn.commit()
    except sqlite3.IntegrityError as exc:
        conn.rollback()
        # Translate the raw sqlite error into a clean, callable-facing
        # exception - callers/routers must never let sqlite3.IntegrityError
        # itself reach an API response.
        raise BookingIntegrityError(
            f"Could not create booking: referenced lead or workspace does not exist ({exc})"
        ) from exc
    finally:
        conn.close()
    return booking


def get_active_booking(lead_id: str, workspace_type: str, date_str: Optional[str] = None) -> Optional[dict]:
    """Finds an existing confirmed booking for this lead + type (+ date, if
    given) - used to stop a duplicate/retried message from booking twice."""
    conn = db.get_connection()
    if date_str:
        row = conn.execute(
            """SELECT * FROM bookings WHERE lead_id = ? AND workspace_type = ? AND date = ?
               AND status = 'confirmed' ORDER BY created_at DESC LIMIT 1""",
            (lead_id, workspace_type, date_str),
        ).fetchone()
    else:
        row = conn.execute(
            """SELECT * FROM bookings WHERE lead_id = ? AND workspace_type = ?
               AND status = 'confirmed' ORDER BY created_at DESC LIMIT 1""",
            (lead_id, workspace_type),
        ).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def get_booking(booking_id: str) -> Optional[dict]:
    conn = db.get_connection()
    row = conn.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def update_status(booking_id: str, status: str) -> Optional[dict]:
    conn = db.get_connection()
    conn.execute("UPDATE bookings SET status = ? WHERE booking_id = ?", (status, booking_id))
    conn.commit()
    row = conn.execute("SELECT * FROM bookings WHERE booking_id = ?", (booking_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def bookings_for_lead(lead_id: str) -> list:
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM bookings WHERE lead_id = ?", (lead_id,)).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]
