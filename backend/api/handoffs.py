from fastapi import APIRouter, HTTPException, Query

from backend.services import handoffs_service

router = APIRouter(prefix="/api/handoffs", tags=["handoffs"])


@router.get("")
def list_handoffs(pending_only: bool = Query(default=False)):
    return handoffs_service.list_handoffs(pending_only=pending_only)


@router.get("/{lead_id}")
def get_handoff(lead_id: str):
    handoff = handoffs_service.get_handoff(lead_id)
    if not handoff:
        raise HTTPException(status_code=404, detail="No handoff on file for this lead")
    return handoff
