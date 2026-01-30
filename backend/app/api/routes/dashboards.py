"""Dashboards APIルート"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Query, Path, HTTPException
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError, ForbiddenError
from app.services.dashboard_service import (
    create_dashboard,
    get_dashboard,
    list_dashboards,
    update_dashboard,
    delete_dashboard,
    clone_dashboard,
    get_referenced_datasets,
)
from app.services.dashboard_share_service import check_dashboard_permission
from app.models.dashboard import Dashboard, DashboardCreate, DashboardUpdate

router = APIRouter(prefix="/dashboards", tags=["dashboards"])


class DashboardResponse(BaseModel):
    dashboard_id: str
    name: str
    owner_id: str
    layout: dict
    filters: list[dict]
    default_filter_view_id: Optional[str]
    created_at: str
    updated_at: str


class DashboardCreateRequest(BaseModel):
    name: str
    layout: dict = {}
    filters: list[dict] = []
    default_filter_view_id: Optional[str] = None


class DashboardUpdateRequest(BaseModel):
    name: Optional[str] = None
    layout: Optional[dict] = None
    filters: Optional[list[dict]] = None
    default_filter_view_id: Optional[str] = None


class CloneDashboardRequest(BaseModel):
    name: Optional[str] = None


@router.get("", response_model=dict)
async def list_dashboards_endpoint(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Dashboard一覧取得"""
    user_id = current_user["user_id"]
    dashboards, total = await list_dashboards(owner_id=user_id, limit=limit, offset=offset, q=q)
    
    return {
        "data": [
            DashboardResponse(
                dashboard_id=d.dashboard_id,
                name=d.name,
                owner_id=d.owner_id,
                layout=d.layout,
                filters=d.filters,
                default_filter_view_id=d.default_filter_view_id,
                created_at=d.created_at.isoformat(),
                updated_at=d.updated_at.isoformat(),
            )
            for d in dashboards
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
        },
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_dashboard_endpoint(
    request: DashboardCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Dashboard作成"""
    user_id = current_user["user_id"]
    dashboard_data = DashboardCreate(
        name=request.name,
        layout=request.layout,
        filters=request.filters,
        default_filter_view_id=request.default_filter_view_id,
    )
    dashboard = await create_dashboard(user_id, dashboard_data)
    
    return {
        "data": DashboardResponse(
            dashboard_id=dashboard.dashboard_id,
            name=dashboard.name,
            owner_id=dashboard.owner_id,
            layout=dashboard.layout,
            filters=dashboard.filters,
            default_filter_view_id=dashboard.default_filter_view_id,
            created_at=dashboard.created_at.isoformat(),
            updated_at=dashboard.updated_at.isoformat(),
        )
    }


@router.get("/{dashboard_id}", response_model=dict)
async def get_dashboard_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    current_user: dict = Depends(get_current_user),
):
    """Dashboard詳細取得"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # 権限チェック
    user_id = current_user["user_id"]
    permission = await check_dashboard_permission(dashboard_id, user_id)
    if not permission:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have permission to view this dashboard",
        )
    
    return {
        "data": DashboardResponse(
            dashboard_id=dashboard.dashboard_id,
            name=dashboard.name,
            owner_id=dashboard.owner_id,
            layout=dashboard.layout,
            filters=dashboard.filters,
            default_filter_view_id=dashboard.default_filter_view_id,
            created_at=dashboard.created_at.isoformat(),
            updated_at=dashboard.updated_at.isoformat(),
        ),
        "permission": permission,
    }


@router.put("/{dashboard_id}", response_model=dict)
async def update_dashboard_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    request: DashboardUpdateRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """Dashboard更新"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # 権限チェック（Editor/Ownerのみ）
    user_id = current_user["user_id"]
    permission = await check_dashboard_permission(dashboard_id, user_id)
    if permission not in ["owner", "editor"]:
        raise ForbiddenError("You don't have permission to update this dashboard")
    
    dashboard_data = DashboardUpdate(
        name=request.name,
        layout=request.layout,
        filters=request.filters,
        default_filter_view_id=request.default_filter_view_id,
    )
    dashboard = await update_dashboard(dashboard_id, dashboard_data)
    
    return {
        "data": DashboardResponse(
            dashboard_id=dashboard.dashboard_id,
            name=dashboard.name,
            owner_id=dashboard.owner_id,
            layout=dashboard.layout,
            filters=dashboard.filters,
            default_filter_view_id=dashboard.default_filter_view_id,
            created_at=dashboard.created_at.isoformat(),
            updated_at=dashboard.updated_at.isoformat(),
        )
    }


@router.delete("/{dashboard_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dashboard_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    current_user: dict = Depends(get_current_user),
):
    """Dashboard削除"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # Ownerのみ削除可能
    user_id = current_user["user_id"]
    if dashboard.owner_id != user_id:
        raise ForbiddenError("You don't have permission to delete this dashboard")
    
    await delete_dashboard(dashboard_id)


@router.post("/{dashboard_id}/clone", response_model=dict, status_code=status.HTTP_201_CREATED)
async def clone_dashboard_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    request: CloneDashboardRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """Dashboard複製"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    user_id = current_user["user_id"]
    dashboard = await clone_dashboard(dashboard_id, user_id, request.name)
    
    return {
        "data": DashboardResponse(
            dashboard_id=dashboard.dashboard_id,
            name=dashboard.name,
            owner_id=dashboard.owner_id,
            layout=dashboard.layout,
            filters=dashboard.filters,
            default_filter_view_id=dashboard.default_filter_view_id,
            created_at=dashboard.created_at.isoformat(),
            updated_at=dashboard.updated_at.isoformat(),
        )
    }


@router.get("/{dashboard_id}/referenced-datasets", response_model=dict)
async def get_referenced_datasets_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    current_user: dict = Depends(get_current_user),
):
    """参照Dataset一覧取得"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # 権限チェック
    user_id = current_user["user_id"]
    permission = await check_dashboard_permission(dashboard_id, user_id)
    if not permission:
        raise ForbiddenError("You don't have permission to view this dashboard")
    
    dataset_ids = await get_referenced_datasets(dashboard_id)
    
    return {
        "data": dataset_ids
    }
