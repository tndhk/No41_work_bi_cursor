"""認証APIルート"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_user
from app.services.user_service import get_user_by_email, get_user
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.core.exceptions import UnauthorizedError, NotFoundError

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


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """ログイン"""
    # ユーザを検索
    user = await get_user_by_email(request.email)
    if not user:
        raise UnauthorizedError("Invalid email or password")
    
    # パスワードを検証
    if not verify_password(request.password, user.password_hash):
        raise UnauthorizedError("Invalid email or password")
    
    # JWTトークンを発行
    access_token = create_access_token(user.user_id)
    
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
async def logout(current_user: dict = Depends(get_current_user)):
    """ログアウト"""
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
