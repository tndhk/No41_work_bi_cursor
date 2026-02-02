"""Chatbot APIルート"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_user
from app.services import chatbot_service
from app.services.chatbot_service import RateLimitExceeded
from app.core.exceptions import NotFoundError

router = APIRouter(prefix="/dashboards", tags=["chatbot"])


class ChatRequest(BaseModel):
    """チャットリクエスト"""
    message: str = Field(..., min_length=1, max_length=2000, description="質問メッセージ")


class ChatResponse(BaseModel):
    """チャットレスポンス"""
    answer: str = Field(..., description="AI回答")
    datasets_used: List[str] = Field(default_factory=list, description="参照されたDataset IDリスト")


@router.post("/{dashboard_id}/chat", response_model=ChatResponse)
async def chat(
    dashboard_id: str,
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """Chatbot質問
    
    Args:
        dashboard_id: Dashboard ID
        request: チャットリクエスト
        current_user: 現在のユーザー
        
    Returns:
        ChatResponse: AI回答とDataset IDリスト
        
    Raises:
        HTTPException: レート制限超過、Dashboardが見つからない、その他のエラー
    """
    try:
        result = await chatbot_service.chat(
            dashboard_id=dashboard_id,
            message=request.message,
            user_id=current_user["user_id"],
        )
        return ChatResponse(
            answer=result["answer"],
            datasets_used=result["datasets_used"],
        )
    except RateLimitExceeded as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(e),
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"チャット処理中にエラーが発生しました: {str(e)}",
        )
