"""依存性注入"""
from typing import Annotated, Optional
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_token
from app.core.exceptions import UnauthorizedError


security = HTTPBearer()


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> dict:
    """現在のユーザを取得"""
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("Invalid authentication credentials")
        request.state.user_id = user_id
        return {"user_id": user_id, "payload": payload}
    except ValueError:
        raise UnauthorizedError("Invalid authentication credentials")


def get_request_id(request: Request) -> Optional[str]:
    """リクエストIDを取得"""
    return getattr(request.state, "request_id", None)
