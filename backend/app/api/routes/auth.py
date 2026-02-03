"""認証APIルート"""
from fastapi import APIRouter, Depends, Request, Response
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_user, get_request_id
from app.services.user_service import get_user_by_email, get_user
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.core.exceptions import UnauthorizedError, NotFoundError
from app.services.audit_log_service import create_audit_log
import uuid

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class UserResponse(BaseModel):
    user_id: str
    email: str
    name: str


def _set_auth_cookies(response: Response, access_token: str, csrf_token: str) -> None:
    secure = settings.auth_cookie_secure or settings.env != "local"
    response.set_cookie(
        key=settings.auth_cookie_name,
        value=access_token,
        httponly=True,
        secure=secure,
        samesite=settings.auth_cookie_samesite,
        max_age=settings.auth_cookie_max_age,
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value=csrf_token,
        httponly=False,
        secure=secure,
        samesite=settings.auth_cookie_samesite,
        max_age=settings.auth_cookie_max_age,
        path="/",
    )


def _clear_auth_cookies(response: Response) -> None:
    secure = settings.auth_cookie_secure or settings.env != "local"
    response.set_cookie(
        key=settings.auth_cookie_name,
        value="",
        httponly=True,
        secure=secure,
        samesite=settings.auth_cookie_samesite,
        max_age=0,
        path="/",
    )
    response.set_cookie(
        key=settings.csrf_cookie_name,
        value="",
        httponly=False,
        secure=secure,
        samesite=settings.auth_cookie_samesite,
        max_age=0,
        path="/",
    )


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request = ..., response: Response = ...):
    """ログイン"""
    # ユーザを検索
    user = await get_user_by_email(request.email)
    if not user:
        # ログイン失敗ログ（ユーザ不存在）
        await create_audit_log(
            event_type="USER_LOGIN_FAILED",
            user_id="unknown",
            target_type="User",
            target_id="unknown",
            details={
                "email": request.email,
                "reason": "user_not_found",
            },
            request_id=get_request_id(http_request),
        )
        raise UnauthorizedError("Invalid email or password")
    
    # パスワードを検証
    if not verify_password(request.password, user.password_hash):
        # ログイン失敗ログ（パスワード不一致）
        await create_audit_log(
            event_type="USER_LOGIN_FAILED",
            user_id=user.user_id,
            target_type="User",
            target_id=user.user_id,
            details={
                "email": request.email,
                "reason": "invalid_password",
            },
            request_id=get_request_id(http_request),
        )
        raise UnauthorizedError("Invalid email or password")
    
    # JWTトークンを発行
    access_token = create_access_token(user.user_id)
    csrf_token = uuid.uuid4().hex
    _set_auth_cookies(response, access_token, csrf_token)
    
    # ログイン成功ログ
    await create_audit_log(
        event_type="USER_LOGIN",
        user_id=user.user_id,
        target_type="User",
        target_id=user.user_id,
        details={
            "email": request.email,
        },
        request_id=get_request_id(http_request),
    )
    
    return LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.jwt_expire_minutes * 60,
        user={
            "user_id": user.user_id,
            "email": user.email,
            "name": user.name,
        },
    )


@router.post("/logout")
async def logout(
    current_user: dict = Depends(get_current_user),
    http_request: Request = ...,
    response: Response = ...,
):
    """ログアウト"""
    # ログアウトログ
    user_id = current_user["user_id"]
    await create_audit_log(
        event_type="USER_LOGOUT",
        user_id=user_id,
        target_type="User",
        target_id=user_id,
        details={},
        request_id=get_request_id(http_request),
    )
    
    _clear_auth_cookies(response)
    return {"message": "ログアウトしました"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """現在のユーザ情報取得"""
    user_id = current_user["user_id"]
    user = await get_user(user_id)
    
    if not user:
        raise NotFoundError("User", user_id)
    
    return UserResponse(
        user_id=user.user_id,
        email=user.email,
        name=user.name,
    )
