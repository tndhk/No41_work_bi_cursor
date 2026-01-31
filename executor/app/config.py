"""Executor設定"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """設定"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # リソース制限（Card実行）
    card_timeout_seconds: int = 10
    card_max_memory_mb: int = 2048
    card_max_file_size_mb: int = 100
    
    # リソース制限（Transform実行）
    transform_timeout_seconds: int = 300
    transform_max_memory_mb: int = 4096
    transform_max_file_size_mb: int = 1000
    
    # 実行キュー設定
    max_concurrent_cards: int = 10
    max_concurrent_transforms: int = 5
    queue_size_cards: int = 50
    queue_size_transforms: int = 20


settings = Settings()
