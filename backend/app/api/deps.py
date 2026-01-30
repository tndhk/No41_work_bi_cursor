"""依存性注入"""
from typing import Annotated
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.core.security import verify_token
from app.core.exceptions import UnauthorizedError


security = HTTPBearer()


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]
) -> dict:
    """現在のユーザを取得"""
    token = credentials.credentials
    
    try:
        payload = verify_token(token)
        user_id: str = payload.get("sub")
        if user_id is None:
            raise UnauthorizedError("Invalid authentication credentials")
        return {"user_id": user_id, "payload": payload}
    except ValueError:
        raise UnauthorizedError("Invalid authentication credentials")
