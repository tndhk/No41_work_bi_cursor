"""設定のテスト"""
import os
import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_loads_from_env():
    """環境変数から設定を読み込む"""
    os.environ["ENV"] = "local"
    os.environ["API_HOST"] = "0.0.0.0"
    os.environ["API_PORT"] = "8000"
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-min-32-chars-long-enough"
    
    settings = Settings()
    assert settings.env == "local"
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000


def test_settings_validates_jwt_secret_length():
    """JWT_SECRET_KEYが32文字未満の場合エラー"""
    os.environ["JWT_SECRET_KEY"] = "short"
    
    with pytest.raises(ValidationError):
        Settings()


def test_settings_has_default_values():
    """デフォルト値が設定されている"""
    os.environ["JWT_SECRET_KEY"] = "test-secret-key-min-32-chars-long-enough"
    os.environ["LOG_LEVEL"] = "INFO"
    
    settings = Settings()
    assert settings.api_workers == 4
    assert settings.jwt_expire_minutes == 1440
    assert settings.log_level == "INFO"
