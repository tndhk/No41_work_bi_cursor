"""Users APIルート"""
from typing import Optional
from fastapi import APIRouter, Depends, Query

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError
from app.services.user_service import get_user, list_users
from app.models.user import UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.get("", response_model=dict)
async def list_users_endpoint(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """ユーザ一覧取得"""
    users, total = await list_users(limit=limit, offset=offset, q=q)
    
    return {
        "data": [UserResponse(**user.dict()) for user in users],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
        },
    }


@router.get("/{user_id}", response_model=dict)
async def get_user_endpoint(
    user_id: str,
    current_user: dict = Depends(get_current_user),
):
    """ユーザ詳細取得"""
    user = await get_user(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    
    return {
        "data": UserResponse(**user.dict(), groups=[]),
    }
