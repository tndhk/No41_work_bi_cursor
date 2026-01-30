"""認証・セキュリティのテスト"""
import pytest
from datetime import datetime, timedelta
from jose import jwt

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    verify_token,
    get_password_hash,
    verify_password_hash,
)


def test_hash_password():
    """パスワードをハッシュ化できる"""
    password = "testpassword123"
    hashed = hash_password(password)
    assert hashed != password
    assert len(hashed) > 0


def test_verify_password_correct():
    """正しいパスワードを検証できる"""
    password = "testpassword123"
    hashed = hash_password(password)
    assert verify_password(password, hashed) is True


def test_verify_password_incorrect():
    """間違ったパスワードを検証できる"""
    password = "testpassword123"
    wrong_password = "wrongpassword"
    hashed = hash_password(password)
    assert verify_password(wrong_password, hashed) is False


def test_create_access_token():
    """アクセストークンを作成できる"""
    user_id = "user_123"
    token = create_access_token(user_id)
    assert token is not None
    assert len(token) > 0


def test_verify_token_valid():
    """有効なトークンを検証できる"""
    user_id = "user_123"
    token = create_access_token(user_id)
    payload = verify_token(token)
    assert payload["sub"] == user_id
    assert payload["type"] == "access"


def test_verify_token_expired():
    """期限切れトークンを検証できない"""
    import os
    from app.core.config import settings
    
    # 期限切れトークンを作成
    expire = datetime.utcnow() - timedelta(minutes=1)
    payload = {
        "sub": "user_123",
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access",
    }
    token = jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)
    
    with pytest.raises(Exception):  # jwt.ExpiredSignatureError
        verify_token(token)


def test_verify_token_invalid():
    """無効なトークンを検証できない"""
    invalid_token = "invalid.token.here"
    
    with pytest.raises(Exception):  # jwt.DecodeError
        verify_token(invalid_token)
