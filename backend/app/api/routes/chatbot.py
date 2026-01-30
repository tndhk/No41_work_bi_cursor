"""Chatbot APIルート"""
from fastapi import APIRouter, Depends

from app.api.deps import get_current_user

router = APIRouter(prefix="/dashboards", tags=["chatbot"])


@router.post("/{dashboard_id}/chat")
async def chat(
    dashboard_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Chatbot質問"""
    # TODO: Vertex AI連携実装
    return {"status": "not_implemented"}
