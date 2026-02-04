"""ミドルウェア"""
import uuid
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import get_logger
from app.core.config import settings
from app.core.exceptions import ForbiddenError

logger = get_logger(__name__)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """リクエストID生成ミドルウェア"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        response = await call_next(request)
        
        duration = time.time() - start_time
        
        logger.info(
            "request_completed",
            request_id=request_id,
            user_id=getattr(request.state, "user_id", None),
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration * 1000, 2),
        )
        
        response.headers["X-Request-ID"] = request_id
        
        return response


class CsrfMiddleware(BaseHTTPMiddleware):
    """CSRF対策ミドルウェア（Double Submit Cookie）"""

    SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
    EXEMPT_PATHS = {"/api/auth/login", "/api/test/setup"}

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.method not in self.SAFE_METHODS and request.url.path.startswith("/api"):
            if request.url.path not in self.EXEMPT_PATHS:
                cookie_token = request.cookies.get(settings.csrf_cookie_name)
                header_token = request.headers.get(settings.csrf_header_name)
                if not cookie_token or not header_token or cookie_token != header_token:
                    raise ForbiddenError("CSRF token missing or invalid")
        return await call_next(request)
