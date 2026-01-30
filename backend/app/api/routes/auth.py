"""認証APIルート"""
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr

from app.api.deps import get_current_user

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
    """ログイン（MVPでは簡易実装）"""
    # TODO: 実際のユーザ認証を実装
    # 現時点ではダミー実装
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Login not implemented yet",
    )


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """ログアウト"""
    return {"message": "ログアウトしました"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """現在のユーザ情報取得"""
    # TODO: 実際のユーザ情報を取得
    # 現時点ではダミー実装
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Get current user not implemented yet",
    )
