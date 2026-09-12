from fastapi import APIRouter, HTTPException

from backend.schemas.bookings import BookingCreate, BookingUpdate
from backend.services import bookings_service

router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.get("")
def list_bookings():
    return bookings_service.list_bookings()


@router.get("/{booking_id}")
def get_booking(booking_id: str):
    booking = bookings_service.get_booking(booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("", status_code=201)
def create_booking(payload: BookingCreate):
    try:
        return bookings_service.create_booking(payload.model_dump())
    except bookings_service.BookingError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.patch("/{booking_id}")
def update_booking(booking_id: str, payload: BookingUpdate):
    updated = bookings_service.update_booking_status(booking_id, payload.status)
    if not updated:
        raise HTTPException(status_code=404, detail="Booking not found")
    return updated
