from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.services import availability_service

router = APIRouter(prefix="/api/workspaces", tags=["availability"])


@router.get("/{workspace_id}/availability")
def get_availability(
    workspace_id: str,
    date: Optional[str] = Query(default=None, description="ISO YYYY-MM-DD, defaults to today"),
    start_time: Optional[str] = Query(default=None, description="HH:MM, informational for meeting rooms"),
    end_time: Optional[str] = Query(default=None, description="HH:MM, informational for meeting rooms"),
    capacity: Optional[int] = Query(default=None, ge=1, description="Seats needed, for a clearer is_available check"),
):
    result = availability_service.check_availability(workspace_id, date_str=date)
    if result is None:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if capacity is not None:
        result["is_available"] = result["slots_remaining"] >= capacity
    if start_time:
        result["start_time"] = start_time
    if end_time:
        result["end_time"] = end_time
    return result
