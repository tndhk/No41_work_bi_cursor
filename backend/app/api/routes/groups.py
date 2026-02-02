"""Groups APIルート"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.services.group_service import (
    create_group,
    get_group,
    list_groups,
    update_group,
    delete_group,
    add_group_member,
    remove_group_member,
    list_group_members,
)
from app.models.group import Group, GroupCreate, GroupUpdate, GroupDetail

router = APIRouter(prefix="/groups", tags=["groups"])


class GroupResponse(BaseModel):
    group_id: str
    name: str
    created_at: str
    updated_at: str


class GroupCreateRequest(BaseModel):
    name: str


class GroupUpdateRequest(BaseModel):
    name: Optional[str] = None


class AddMemberRequest(BaseModel):
    user_id: str


@router.get("", response_model=dict)
async def list_groups_endpoint(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """グループ一覧取得"""
    groups, total = await list_groups(limit=limit, offset=offset, q=q)
    
    return {
        "data": [
            GroupResponse(
                group_id=g.group_id,
                name=g.name,
                created_at=g.created_at.isoformat(),
                updated_at=g.updated_at.isoformat(),
            )
            for g in groups
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
        },
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_group_endpoint(
    request: GroupCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """グループ作成"""
    group_data = GroupCreate(name=request.name)
    group = await create_group(group_data)
    
    return {
        "data": GroupResponse(
            group_id=group.group_id,
            name=group.name,
            created_at=group.created_at.isoformat(),
            updated_at=group.updated_at.isoformat(),
        )
    }


@router.get("/{group_id}", response_model=dict)
async def get_group_endpoint(
    group_id: str = Path(..., description="グループID"),
    current_user: dict = Depends(get_current_user),
):
    """グループ詳細取得"""
    group = await get_group(group_id)
    if not group:
        raise NotFoundError("Group", group_id)
    
    members = await list_group_members(group_id)
    
    return {
        "data": GroupDetail(
            group_id=group.group_id,
            name=group.name,
            created_at=group.created_at,
            updated_at=group.updated_at,
            members=members,
        ).model_dump()
    }


@router.put("/{group_id}", response_model=dict)
async def update_group_endpoint(
    group_id: str = Path(..., description="グループID"),
    request: GroupUpdateRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """グループ更新"""
    group_data = GroupUpdate(name=request.name)
    group = await update_group(group_id, group_data)
    
    return {
        "data": GroupResponse(
            group_id=group.group_id,
            name=group.name,
            created_at=group.created_at.isoformat(),
            updated_at=group.updated_at.isoformat(),
        )
    }


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group_endpoint(
    group_id: str = Path(..., description="グループID"),
    current_user: dict = Depends(get_current_user),
):
    """グループ削除"""
    await delete_group(group_id)


@router.post("/{group_id}/members", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_group_member_endpoint(
    group_id: str = Path(..., description="グループID"),
    request: AddMemberRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """グループにメンバーを追加"""
    member = await add_group_member(group_id, request.user_id)
    
    return {
        "data": {
            "group_id": member.group_id,
            "user_id": member.user_id,
            "added_at": member.added_at.isoformat(),
        }
    }


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_group_member_endpoint(
    group_id: str = Path(..., description="グループID"),
    user_id: str = Path(..., description="ユーザID"),
    current_user: dict = Depends(get_current_user),
):
    """グループからメンバーを削除"""
    await remove_group_member(group_id, user_id)
