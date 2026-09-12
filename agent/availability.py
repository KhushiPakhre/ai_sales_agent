"""
Per-date calendar availability for day passes / meeting rooms.

Phase 2 introduced this as a JSON-file-backed calendar; Phase 3 moves the
same model onto the `availability` table in db.py. The public functions
(get_available_slots / reserve / release) keep the same signatures on
purpose - recommender.py doesn't need to change to pick up the DB.
"""
from agent import db


def get_available_slots(workspace_id: str, date_str: str, daily_capacity: int) -> int:
    """Slots left for this workspace on this date. Untouched dates default
    to the workspace's full daily capacity - nothing is reserved until a
    booking actually happens."""
    conn = db.get_connection()
    row = conn.execute(
        "SELECT slots_remaining FROM availability WHERE workspace_id = ? AND date = ?",
        (workspace_id, date_str),
    ).fetchone()
    conn.close()
    return row["slots_remaining"] if row else daily_capacity


def reserve(workspace_id: str, date_str: str, seats: int, daily_capacity: int) -> bool:
    """Reserves `seats` on `date_str` if enough capacity remains that day.
    Returns False (and reserves nothing) if there isn't enough left."""
    seats = max(1, seats)
    conn = db.get_connection()
    row = conn.execute(
        "SELECT slots_remaining FROM availability WHERE workspace_id = ? AND date = ?",
        (workspace_id, date_str),
    ).fetchone()
    remaining = row["slots_remaining"] if row else daily_capacity
    if remaining < seats:
        conn.close()
        return False
    conn.execute(
        """INSERT INTO availability (workspace_id, date, slots_remaining) VALUES (?, ?, ?)
           ON CONFLICT(workspace_id, date) DO UPDATE SET slots_remaining = excluded.slots_remaining""",
        (workspace_id, date_str, remaining - seats),
    )
    conn.commit()
    conn.close()
    return True


def release(workspace_id: str, date_str: str, seats: int, daily_capacity: int) -> None:
    """Returns `seats` back to a date's availability - used on cancellation
    or a booking marked no-show, so the slot isn't lost forever."""
    seats = max(1, seats)
    conn = db.get_connection()
    row = conn.execute(
        "SELECT slots_remaining FROM availability WHERE workspace_id = ? AND date = ?",
        (workspace_id, date_str),
    ).fetchone()
    remaining = row["slots_remaining"] if row else daily_capacity
    new_remaining = min(daily_capacity, remaining + seats)
    conn.execute(
        """INSERT INTO availability (workspace_id, date, slots_remaining) VALUES (?, ?, ?)
           ON CONFLICT(workspace_id, date) DO UPDATE SET slots_remaining = excluded.slots_remaining""",
        (workspace_id, date_str, new_remaining),
    )
    conn.commit()
    conn.close()
