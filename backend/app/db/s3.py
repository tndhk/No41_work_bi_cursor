"""S3接続層"""
from typing import Literal
import aioboto3
from botocore.config import Config

from app.core.config import settings


_s3_client = None


def get_bucket_name(bucket_type: Literal["datasets", "static"]) -> str:
    """バケット名を取得"""
    bucket_map = {
        "datasets": settings.s3_bucket_datasets,
        "static": settings.s3_bucket_static,
    }
    
    if bucket_type not in bucket_map:
        raise ValueError(f"Unknown bucket type: {bucket_type}")
    
    return bucket_map[bucket_type]


async def get_s3_client():
    """S3クライアントを取得（シングルトン）"""
    global _s3_client
    
    if _s3_client is None:
        session = aioboto3.Session()
        config = Config(
            region_name=settings.s3_region,
            retries={"max_attempts": 3, "mode": "adaptive"},
        )
        
        client_kwargs = {
            "config": config,
        }
        
        if settings.s3_endpoint:
            client_kwargs["endpoint_url"] = settings.s3_endpoint
        
        if settings.s3_access_key and settings.s3_secret_key:
            client_kwargs["aws_access_key_id"] = settings.s3_access_key
            client_kwargs["aws_secret_access_key"] = settings.s3_secret_key
        
        _s3_client = session.client("s3", **client_kwargs)
    
    return _s3_client


async def close_s3():
    """S3接続を閉じる"""
    global _s3_client
    
    if _s3_client:
        await _s3_client.close()
        _s3_client = None
