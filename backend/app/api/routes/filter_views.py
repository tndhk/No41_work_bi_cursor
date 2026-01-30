"""FilterViews APIルート"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Path
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError, ForbiddenError
from app.services.filter_view_service import (
    create_filter_view,
    get_filter_view,
    list_filter_views,
    update_filter_view,
    delete_filter_view,
)
from app.services.dashboard_service import get_dashboard
from app.services.dashboard_share_service import check_dashboard_permission

router = APIRouter(prefix="/dashboards/{dashboard_id}/filter-views", tags=["filter-views"])


class FilterViewResponse(BaseModel):
    filter_view_id: str
    dashboard_id: str
    name: str
    owner_id: str
    filter_state: dict
    is_shared: bool
    is_default: bool
    created_at: str
    updated_at: str


class CreateFilterViewRequest(BaseModel):
    name: str
    filter_state: dict
    is_shared: bool = False
    is_default: bool = False


class UpdateFilterViewRequest(BaseModel):
    name: Optional[str] = None
    filter_state: Optional[dict] = None
    is_shared: Optional[bool] = None
    is_default: Optional[bool] = None


@router.get("", response_model=dict)
async def list_filter_views_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    current_user: dict = Depends(get_current_user),
):
    """FilterView一覧取得"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # 権限チェック
    user_id = current_user["user_id"]
    permission = await check_dashboard_permission(dashboard_id, user_id)
    if not permission:
        raise ForbiddenError("You don't have permission to view this dashboard")
    
    filter_views = await list_filter_views(dashboard_id)
    
    # 共有ビューと個人ビューをフィルタ
    user_filter_views = [
        fv for fv in filter_views
        if fv.is_shared or fv.owner_id == user_id
    ]
    
    return {
        "data": [
            FilterViewResponse(
                filter_view_id=fv.filter_view_id,
                dashboard_id=fv.dashboard_id,
                name=fv.name,
                owner_id=fv.owner_id,
                filter_state=fv.filter_state,
                is_shared=fv.is_shared,
                is_default=fv.is_default,
                created_at=fv.created_at.isoformat(),
                updated_at=fv.updated_at.isoformat(),
            )
            for fv in user_filter_views
        ]
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_filter_view_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    request: CreateFilterViewRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """FilterView作成"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # Editor/Ownerのみ作成可能
    user_id = current_user["user_id"]
    permission = await check_dashboard_permission(dashboard_id, user_id)
    if permission not in ["owner", "editor"]:
        raise ForbiddenError("You don't have permission to create filter views")
    
    filter_view = await create_filter_view(
        dashboard_id=dashboard_id,
        name=request.name,
        owner_id=user_id,
        filter_state=request.filter_state,
        is_shared=request.is_shared,
        is_default=request.is_default,
    )
    
    return {
        "data": FilterViewResponse(
            filter_view_id=filter_view.filter_view_id,
            dashboard_id=filter_view.dashboard_id,
            name=filter_view.name,
            owner_id=filter_view.owner_id,
            filter_state=filter_view.filter_state,
            is_shared=filter_view.is_shared,
            is_default=filter_view.is_default,
            created_at=filter_view.created_at.isoformat(),
            updated_at=filter_view.updated_at.isoformat(),
        )
    }


@router.get("/{filter_view_id}", response_model=dict)
async def get_filter_view_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    filter_view_id: str = Path(..., description="FilterView ID"),
    current_user: dict = Depends(get_current_user),
):
    """FilterView詳細取得"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # 権限チェック
    user_id = current_user["user_id"]
    permission = await check_dashboard_permission(dashboard_id, user_id)
    if not permission:
        raise ForbiddenError("You don't have permission to view this dashboard")
    
    filter_view = await get_filter_view(filter_view_id)
    if not filter_view:
        raise NotFoundError("FilterView", filter_view_id)
    
    # 共有ビューまたは所有者のみアクセス可能
    if not filter_view.is_shared and filter_view.owner_id != user_id:
        raise ForbiddenError("You don't have permission to view this filter view")
    
    return {
        "data": FilterViewResponse(
            filter_view_id=filter_view.filter_view_id,
            dashboard_id=filter_view.dashboard_id,
            name=filter_view.name,
            owner_id=filter_view.owner_id,
            filter_state=filter_view.filter_state,
            is_shared=filter_view.is_shared,
            is_default=filter_view.is_default,
            created_at=filter_view.created_at.isoformat(),
            updated_at=filter_view.updated_at.isoformat(),
        )
    }


@router.put("/{filter_view_id}", response_model=dict)
async def update_filter_view_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    filter_view_id: str = Path(..., description="FilterView ID"),
    request: UpdateFilterViewRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """FilterView更新"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    filter_view = await get_filter_view(filter_view_id)
    if not filter_view:
        raise NotFoundError("FilterView", filter_view_id)
    
    # 所有者のみ更新可能
    user_id = current_user["user_id"]
    if filter_view.owner_id != user_id:
        raise ForbiddenError("You don't have permission to update this filter view")
    
    filter_view = await update_filter_view(
        filter_view_id=filter_view_id,
        name=request.name,
        filter_state=request.filter_state,
        is_shared=request.is_shared,
        is_default=request.is_default,
    )
    
    return {
        "data": FilterViewResponse(
            filter_view_id=filter_view.filter_view_id,
            dashboard_id=filter_view.dashboard_id,
            name=filter_view.name,
            owner_id=filter_view.owner_id,
            filter_state=filter_view.filter_state,
            is_shared=filter_view.is_shared,
            is_default=filter_view.is_default,
            created_at=filter_view.created_at.isoformat(),
            updated_at=filter_view.updated_at.isoformat(),
        )
    }


@router.delete("/{filter_view_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_filter_view_endpoint(
    dashboard_id: str = Path(..., description="Dashboard ID"),
    filter_view_id: str = Path(..., description="FilterView ID"),
    current_user: dict = Depends(get_current_user),
):
    """FilterView削除"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    filter_view = await get_filter_view(filter_view_id)
    if not filter_view:
        raise NotFoundError("FilterView", filter_view_id)
    
    # 所有者のみ削除可能
    user_id = current_user["user_id"]
    if filter_view.owner_id != user_id:
        raise ForbiddenError("You don't have permission to delete this filter view")
    
    await delete_filter_view(filter_view_id)
