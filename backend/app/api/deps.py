"""依存性注入"""
from typing import Annotated, Optional
from fastapi import Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_token
from app.core.config import settings
from app.core.exceptions import UnauthorizedError


security = HTTPBearer(auto_error=False)


async def get_current_user(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
) -> dict:
    """現在のユーザを取得"""
    token = credentials.credentials if credentials else None
    if not token:
        token = request.cookies.get(settings.auth_cookie_name)
    if not token:
        raise UnauthorizedError("Invalid authentication credentials")
    
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
