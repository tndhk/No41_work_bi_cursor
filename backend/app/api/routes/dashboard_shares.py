"""Dashboard Shares APIルート"""
from fastapi import APIRouter, Depends, status, Path
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError, ForbiddenError
from app.services.dashboard_share_service import (
    create_share,
    get_share,
    list_shares,
    update_share,
    delete_share,
    check_dashboard_permission,
)
from app.services.dashboard_service import get_dashboard

router = APIRouter(prefix="/dashboards/{dashboard_id}/shares", tags=["dashboard-shares"])


class ShareResponse(BaseModel):
    share_id: str
    dashboard_id: str
    shared_to_type: str
    shared_to_id: str
    permission: str
    shared_by: str
    created_at: str


class CreateShareRequest(BaseModel):
    shared_to_type: str  # "user" | "group"
    shared_to_id: str
    permission: str  # "owner" | "editor" | "viewer"


class UpdateShareRequest(BaseModel):
    permission: str  # "owner" | "editor" | "viewer"


@router.get("", response_model=dict)
async def list_shares_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    current_user: dict = Depends(get_current_user),
):
    """共有一覧取得"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # Ownerのみ共有一覧を取得可能
    user_id = current_user["user_id"]
    if dashboard.owner_id != user_id:
        raise ForbiddenError("You don't have permission to view shares")
    
    shares = await list_shares(dashboard_id)
    
    return {
        "data": [
            ShareResponse(
                share_id=s.share_id,
                dashboard_id=s.dashboard_id,
                shared_to_type=s.shared_to_type,
                shared_to_id=s.shared_to_id,
                permission=s.permission,
                shared_by=s.shared_by,
                created_at=s.created_at.isoformat(),
            )
            for s in shares
        ]
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_share_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    request: CreateShareRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """共有追加"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # Ownerのみ共有可能
    user_id = current_user["user_id"]
    if dashboard.owner_id != user_id:
        raise ForbiddenError("You don't have permission to share this dashboard")
    
    share = await create_share(
        dashboard_id=dashboard_id,
        shared_to_type=request.shared_to_type,
        shared_to_id=request.shared_to_id,
        permission=request.permission,
        shared_by=user_id,
    )
    
    return {
        "data": ShareResponse(
            share_id=share.share_id,
            dashboard_id=share.dashboard_id,
            shared_to_type=share.shared_to_type,
            shared_to_id=share.shared_to_id,
            permission=share.permission,
            shared_by=share.shared_by,
            created_at=share.created_at.isoformat(),
        )
    }


@router.put("/{share_id}", response_model=dict)
async def update_share_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    share_id: str = Path(..., description="Share ID"),
    request: UpdateShareRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """共有更新"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # Ownerのみ共有更新可能
    user_id = current_user["user_id"]
    if dashboard.owner_id != user_id:
        raise ForbiddenError("You don't have permission to update shares")
    
    share = await update_share(share_id, request.permission)
    
    return {
        "data": ShareResponse(
            share_id=share.share_id,
            dashboard_id=share.dashboard_id,
            shared_to_type=share.shared_to_type,
            shared_to_id=share.shared_to_id,
            permission=share.permission,
            shared_by=share.shared_by,
            created_at=share.created_at.isoformat(),
        )
    }


@router.delete("/{share_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_share_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    share_id: str = Path(..., description="Share ID"),
    current_user: dict = Depends(get_current_user),
):
    """共有削除"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # Ownerのみ共有削除可能
    user_id = current_user["user_id"]
    if dashboard.owner_id != user_id:
        raise ForbiddenError("You don't have permission to delete shares")
    
    await delete_share(share_id)
