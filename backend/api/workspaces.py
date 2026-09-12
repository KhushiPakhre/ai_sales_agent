from typing import Optional
from fastapi import APIRouter, HTTPException, Query

from backend.schemas.workspaces import WorkspaceCreate, WorkspaceUpdate
from backend.services import workspaces_service

router = APIRouter(prefix="/api/workspaces", tags=["workspaces"])


@router.get("")
def list_workspaces(
    city: Optional[str] = None,
    workspace_type: Optional[str] = None,
    min_capacity: Optional[int] = Query(default=None, ge=1),
    max_price: Optional[int] = Query(default=None, ge=0),
    amenity: Optional[str] = None,
):
    return workspaces_service.list_workspaces(
        city=city, workspace_type=workspace_type,
        min_capacity=min_capacity, max_price=max_price, amenity=amenity,
    )


@router.get("/{workspace_id}")
def get_workspace(workspace_id: str):
    ws = workspaces_service.get_workspace_detail(workspace_id)
    if not ws:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return ws


@router.post("", status_code=201)
def create_workspace(payload: WorkspaceCreate):
    return workspaces_service.create_workspace(payload.model_dump())


@router.patch("/{workspace_id}")
def update_workspace(workspace_id: str, payload: WorkspaceUpdate):
    updated = workspaces_service.update_workspace(workspace_id, payload.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return updated
