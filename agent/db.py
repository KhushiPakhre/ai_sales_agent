"""
Phase 3: real database backing for leads, inventory, availability, and
bookings - replacing the flat JSON files from Phases 1-2 (sessions.json,
workspaces.json, calendar.json, bookings.json).

Deliberately kept to Python's built-in sqlite3 rather than adding a new
dependency/ORM: the goal here is a real, queryable, concurrent-safe-enough
store with actual schema and constraints, not a specific vendor choice.
Swapping this for Postgres later is a matter of changing DB_PATH/connection
setup in this one file - every other module talks to session_store.py,
availability.py, recommender.py, and booking_store.py, none of which know
or care that SQLite is underneath.
"""
import json
import os
import sqlite3
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "qdesq.db")
SEED_WORKSPACES_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "workspaces.seed.json")

SCHEMA = """
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT NOT NULL,
    workspace_type TEXT NOT NULL,
    capacity_min INTEGER NOT NULL,
    capacity_max INTEGER NOT NULL,
    price_per_seat_inr INTEGER NOT NULL,
    amenities TEXT NOT NULL,          -- JSON array
    available_from TEXT NOT NULL,
    rating REAL NOT NULL,
    daily_capacity INTEGER            -- only meaningful for day_pass / meeting_room
);

CREATE TABLE IF NOT EXISTS availability (
    workspace_id TEXT NOT NULL,
    date TEXT NOT NULL,               -- ISO YYYY-MM-DD
    slots_remaining INTEGER NOT NULL,
    PRIMARY KEY (workspace_id, date),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);

CREATE TABLE IF NOT EXISTS leads (
    lead_id TEXT PRIMARY KEY,
    channel TEXT,
    company_name TEXT,
    contact_name TEXT,
    location TEXT,
    team_size INTEGER,
    workspace_type TEXT,
    budget_per_seat INTEGER,
    move_in_timeline TEXT,
    requested_date TEXT,
    requested_time TEXT,
    raw_text TEXT,
    extraction_notes TEXT,             -- JSON array
    tier TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS conversation_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    lead_id TEXT NOT NULL,
    channel TEXT,
    direction TEXT NOT NULL,           -- "inbound" | "outbound"
    text TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
);

CREATE TABLE IF NOT EXISTS lead_recommendations_cache (
    lead_id TEXT PRIMARY KEY,
    workspaces_json TEXT NOT NULL,     -- JSON array of workspace dicts last shown
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
);

CREATE TABLE IF NOT EXISTS tours (
    lead_id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    workspace_name TEXT NOT NULL,
    proposed_time TEXT NOT NULL,
    status TEXT NOT NULL,              -- "proposed" | "confirmed" | "reminded" | "no_show" | "completed"
    reminder_sent INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id)
);

CREATE TABLE IF NOT EXISTS bookings (
    booking_id TEXT PRIMARY KEY,
    lead_id TEXT NOT NULL,
    workspace_id TEXT NOT NULL,
    workspace_name TEXT NOT NULL,
    workspace_type TEXT NOT NULL,
    city TEXT NOT NULL,
    date TEXT NOT NULL,
    time TEXT,
    seats INTEGER NOT NULL,
    status TEXT NOT NULL,              -- "confirmed" | "cancelled" | "no_show" | "completed"
    created_at TEXT NOT NULL,
    FOREIGN KEY (lead_id) REFERENCES leads(lead_id),
    FOREIGN KEY (workspace_id) REFERENCES workspaces(id)
);
"""


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Creates tables if missing and seeds inventory on first run.

    Safe to call on every startup - CREATE TABLE IF NOT EXISTS and an
    empty-check before seeding make this idempotent, which is what a real
    migration runner would give you without one being set up here.
    """
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()

    count = conn.execute("SELECT COUNT(*) AS c FROM workspaces").fetchone()["c"]
    if count == 0 and os.path.exists(SEED_WORKSPACES_PATH):
        with open(SEED_WORKSPACES_PATH, "r") as f:
            workspaces = json.load(f)
        for w in workspaces:
            conn.execute(
                """INSERT INTO workspaces
                   (id, name, city, workspace_type, capacity_min, capacity_max,
                    price_per_seat_inr, amenities, available_from, rating, daily_capacity)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    w["id"], w["name"], w["city"], w["workspace_type"],
                    w["capacity_min"], w["capacity_max"], w["price_per_seat_inr"],
                    json.dumps(w.get("amenities", [])), w["available_from"], w["rating"],
                    w.get("daily_capacity"),
                ),
            )
        conn.commit()
    conn.close()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def reset_db() -> None:
    """Demo/test convenience - drops the DB file entirely so init_db() re-seeds clean."""
    conn = get_connection()
    conn.close()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
