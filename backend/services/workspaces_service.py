"""
Inventory (workspace) read/write access.

Reads reuse agent.recommender's row-shaping so the JSON shape returned to
the frontend matches what the agent itself works with. Writes (create/
update) are new - the existing agent code never needed to mutate
inventory - so they talk to agent.db directly rather than inventing a
parallel store. This does not touch agent/db.py's schema or any existing
function.
"""
import json
from typing import List, Optional

from agent import db
from agent.recommender import _row_to_dict, get_workspace  # reuse existing row shaping


def list_workspaces(
    city: Optional[str] = None,
    workspace_type: Optional[str] = None,
    min_capacity: Optional[int] = None,
    max_price: Optional[int] = None,
    amenity: Optional[str] = None,
) -> List[dict]:
    conn = db.get_connection()
    rows = conn.execute("SELECT * FROM workspaces").fetchall()
    conn.close()
    workspaces = [_row_to_dict(r) for r in rows]

    if city:
        workspaces = [w for w in workspaces if w["city"].lower() == city.lower()]
    if workspace_type:
        workspaces = [w for w in workspaces if w["workspace_type"] == workspace_type]
    if min_capacity is not None:
        workspaces = [w for w in workspaces if w["capacity_max"] >= min_capacity]
    if max_price is not None:
        workspaces = [w for w in workspaces if w["price_per_seat_inr"] <= max_price]
    if amenity:
        workspaces = [
            w for w in workspaces
            if any(amenity.lower() in a.lower() for a in w["amenities"])
        ]
    return workspaces


def get_workspace_detail(workspace_id: str) -> Optional[dict]:
    return get_workspace(workspace_id)


def _new_id(conn) -> str:
    row = conn.execute("SELECT COUNT(*) AS c FROM workspaces").fetchone()
    return f"WS{row['c'] + 1:03d}"


def create_workspace(payload: dict) -> dict:
    conn = db.get_connection()
    workspace_id = payload.get("id") or _new_id(conn)
    conn.execute(
        """INSERT INTO workspaces
           (id, name, city, workspace_type, capacity_min, capacity_max,
            price_per_seat_inr, amenities, available_from, rating, daily_capacity)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            workspace_id, payload["name"], payload["city"], payload["workspace_type"],
            payload["capacity_min"], payload["capacity_max"], payload["price_per_seat_inr"],
            json.dumps(payload.get("amenities", [])), payload.get("available_from", "immediate"),
            payload.get("rating", 4.0), payload.get("daily_capacity"),
        ),
    )
    conn.commit()
    conn.close()
    return get_workspace(workspace_id)


def update_workspace(workspace_id: str, payload: dict) -> Optional[dict]:
    existing = get_workspace(workspace_id)
    if not existing:
        return None
    fields = {k: v for k, v in payload.items() if v is not None}
    if not fields:
        return existing
    merged = {**existing, **fields}
    conn = db.get_connection()
    conn.execute(
        """UPDATE workspaces SET name=?, city=?, workspace_type=?, capacity_min=?,
           capacity_max=?, price_per_seat_inr=?, amenities=?, available_from=?,
           rating=?, daily_capacity=? WHERE id=?""",
        (
            merged["name"], merged["city"], merged["workspace_type"], merged["capacity_min"],
            merged["capacity_max"], merged["price_per_seat_inr"], json.dumps(merged["amenities"]),
            merged["available_from"], merged["rating"], merged["daily_capacity"], workspace_id,
        ),
    )
    conn.commit()
    conn.close()
    return get_workspace(workspace_id)
