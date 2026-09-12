from fastapi import APIRouter, HTTPException

from backend.schemas.leads import LeadCreate, LeadUpdate
from backend.services import leads_service

router = APIRouter(prefix="/api/leads", tags=["leads"])


@router.get("")
def list_leads():
    return leads_service.list_leads()


@router.get("/{lead_id}")
def get_lead(lead_id: str):
    detail = leads_service.get_lead_detail(lead_id)
    if not detail:
        raise HTTPException(status_code=404, detail="Lead not found")
    return detail


@router.post("", status_code=201)
def create_lead(payload: LeadCreate):
    return leads_service.create_lead(payload.model_dump())


@router.patch("/{lead_id}")
def update_lead(lead_id: str, payload: LeadUpdate):
    updated = leads_service.update_lead(lead_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Lead not found")
    return updated
