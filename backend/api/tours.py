from fastapi import APIRouter, HTTPException

from backend.schemas.tours import TourCreate, TourUpdate
from backend.services import tours_service

router = APIRouter(prefix="/api/tours", tags=["tours"])


@router.get("")
def list_tours():
    return tours_service.list_tours()


@router.get("/{tour_id}")
def get_tour(tour_id: str):
    # tour_id == lead_id in the existing schema (one active tour per lead) -
    # see backend/services/tours_service.py for why.
    tour = tours_service.get_tour(tour_id)
    if not tour:
        raise HTTPException(status_code=404, detail="Tour not found")
    return tour


@router.post("", status_code=201)
def create_tour(payload: TourCreate):
    try:
        return tours_service.create_tour(payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.patch("/{tour_id}")
def update_tour(tour_id: str, payload: TourUpdate):
    updated = tours_service.update_tour(tour_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Tour not found")
    return updated
