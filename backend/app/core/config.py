"""アプリケーション設定"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """アプリケーション設定"""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    # 環境
    env: str = "local"
    
    # API設定
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_workers: int = 4
    api_debug: bool = False
    
    # 認証設定
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440
    password_min_length: int = 8
    
    # DynamoDB設定
    dynamodb_endpoint: str | None = None
    dynamodb_region: str = "ap-northeast-1"
    dynamodb_table_prefix: str = "bi_"
    
    # S3設定
    s3_endpoint: str | None = None
    s3_region: str = "ap-northeast-1"
    s3_bucket_datasets: str = "bi-datasets"
    s3_bucket_static: str = "bi-static"
    s3_access_key: str | None = None
    s3_secret_key: str | None = None
    
    # Vertex AI設定
    vertex_ai_project_id: str | None = None
    vertex_ai_location: str = "asia-northeast1"
    vertex_ai_model: str = "gemini-1.5-pro"
    
    # 実行基盤設定
    executor_endpoint: str = "http://executor:8080"
    executor_timeout_card: int = 10
    executor_timeout_transform: int = 300
    executor_max_concurrent_cards: int = 10
    executor_max_concurrent_transforms: int = 5
    
    # ログ設定
    log_level: str = "INFO"
    log_format: str = "json"
    
    # テスト設定
    allow_test_setup: bool = False
    
    # キャッシュ設定
    redis_url: str | None = None  # Redis URL（例: redis://localhost:6379/0）
    cache_ttl_seconds: int = 3600  # キャッシュTTL（デフォルト1時間）
    
    def model_post_init(self, __context):
        """バリデーション"""
        if len(self.jwt_secret_key) < 32:
            raise ValueError("JWT_SECRET_KEY must be at least 32 characters")


settings = Settings()
