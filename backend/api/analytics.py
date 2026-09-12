from fastapi import APIRouter

from backend.services import analytics_service

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("")
def get_analytics():
    return analytics_service.get_analytics()
