"""Cards APIルート"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Query, Path, Request
from pydantic import BaseModel

from app.api.deps import get_current_user, get_request_id
from app.core.exceptions import NotFoundError, ForbiddenError, ExecutionError
from app.services.card_service import (
    create_card,
    get_card,
    list_cards,
    update_card,
    delete_card,
    preview_card,
)
from app.models.card import Card, CardCreate, CardUpdate, CardPreviewRequest, CardPreviewResponse
from app.services.audit_log_service import create_audit_log

router = APIRouter(prefix="/cards", tags=["cards"])


class CardResponse(BaseModel):
    card_id: str
    name: str
    owner_id: str
    dataset_id: str
    code: str
    params: dict
    used_columns: list[str]
    filter_applicable: list[str]
    created_at: str
    updated_at: str


class CardCreateRequest(BaseModel):
    name: str
    dataset_id: str
    code: str
    params: dict = {}
    used_columns: list[str] = []
    filter_applicable: list[str] = []


class CardUpdateRequest(BaseModel):
    name: Optional[str] = None
    dataset_id: Optional[str] = None
    code: Optional[str] = None
    params: Optional[dict] = None
    used_columns: Optional[list[str]] = None
    filter_applicable: Optional[list[str]] = None


@router.get("", response_model=dict)
async def list_cards_endpoint(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    dataset_id: Optional[str] = Query(None),
    q: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Card一覧取得"""
    user_id = current_user["user_id"]
    cards, total = await list_cards(owner_id=user_id, dataset_id=dataset_id, limit=limit, offset=offset, q=q)
    
    return {
        "data": [
            CardResponse(
                card_id=c.card_id,
                name=c.name,
                owner_id=c.owner_id,
                dataset_id=c.dataset_id,
                code=c.code,
                params=c.params,
                used_columns=c.used_columns,
                filter_applicable=c.filter_applicable,
                created_at=c.created_at.isoformat(),
                updated_at=c.updated_at.isoformat(),
            )
            for c in cards
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
        },
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_card_endpoint(
    request: CardCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Card作成"""
    user_id = current_user["user_id"]
    card_data = CardCreate(
        name=request.name,
        dataset_id=request.dataset_id,
        code=request.code,
        params=request.params,
        used_columns=request.used_columns,
        filter_applicable=request.filter_applicable,
    )
    
    card = await create_card(user_id, card_data)
    
    return {
        "data": CardResponse(
            card_id=card.card_id,
            name=card.name,
            owner_id=card.owner_id,
            dataset_id=card.dataset_id,
            code=card.code,
            params=card.params,
            used_columns=card.used_columns,
            filter_applicable=card.filter_applicable,
            created_at=card.created_at.isoformat(),
            updated_at=card.updated_at.isoformat(),
        )
    }


@router.get("/{card_id}", response_model=dict)
async def get_card_endpoint(
    card_id: str = Path(..., description="Card ID"),
    current_user: dict = Depends(get_current_user),
):
    """Card詳細取得"""
    card = await get_card(card_id)
    if not card:
        raise NotFoundError("Card", card_id)
    
    return {
        "data": CardResponse(
            card_id=card.card_id,
            name=card.name,
            owner_id=card.owner_id,
            dataset_id=card.dataset_id,
            code=card.code,
            params=card.params,
            used_columns=card.used_columns,
            filter_applicable=card.filter_applicable,
            created_at=card.created_at.isoformat(),
            updated_at=card.updated_at.isoformat(),
        )
    }


@router.put("/{card_id}", response_model=dict)
async def update_card_endpoint(
    card_id: str = Path(..., description="Card ID"),
    request: CardUpdateRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """Card更新"""
    card = await get_card(card_id)
    if not card:
        raise NotFoundError("Card", card_id)
    
    # 所有者チェック
    if card.owner_id != current_user["user_id"]:
        raise ForbiddenError("You don't have permission to update this card")
    
    card_data = CardUpdate(
        name=request.name,
        dataset_id=request.dataset_id,
        code=request.code,
        params=request.params,
        used_columns=request.used_columns,
        filter_applicable=request.filter_applicable,
    )
    
    card = await update_card(card_id, card_data)
    
    return {
        "data": CardResponse(
            card_id=card.card_id,
            name=card.name,
            owner_id=card.owner_id,
            dataset_id=card.dataset_id,
            code=card.code,
            params=card.params,
            used_columns=card.used_columns,
            filter_applicable=card.filter_applicable,
            created_at=card.created_at.isoformat(),
            updated_at=card.updated_at.isoformat(),
        )
    }


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_card_endpoint(
    card_id: str = Path(..., description="Card ID"),
    current_user: dict = Depends(get_current_user),
):
    """Card削除"""
    card = await get_card(card_id)
    if not card:
        raise NotFoundError("Card", card_id)
    
    # 所有者チェック
    if card.owner_id != current_user["user_id"]:
        raise ForbiddenError("You don't have permission to delete this card")
    
    await delete_card(card_id)


@router.post("/{card_id}/preview", response_model=dict)
async def preview_card_endpoint(
    card_id: str = Path(..., description="Card ID"),
    request: CardPreviewRequest = ...,
    current_user: dict = Depends(get_current_user),
    http_request: Request = ...,
):
    """Cardプレビュー実行"""
    card = await get_card(card_id)
    if not card:
        raise NotFoundError("Card", card_id)
    
    user_id = current_user["user_id"]
    
    try:
        preview = await preview_card(card_id, request)
    except NotImplementedError:
        # 未実装エラーは監査ログに記録しない（実装待ちのため）
        raise ExecutionError("Card preview execution will be implemented in Phase 6 (Executor)")
    except Exception as e:
        # 実行失敗ログ
        await create_audit_log(
            event_type="CARD_EXECUTION_FAILED",
            user_id=user_id,
            target_type="Card",
            target_id=card_id,
            details={
                "card_name": card.name,
                "error_message": str(e),
            },
            request_id=get_request_id(http_request),
        )
        raise ExecutionError(str(e))
    
    return {
        "data": preview.model_dump()
    }
