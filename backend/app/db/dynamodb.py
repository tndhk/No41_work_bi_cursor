"""DynamoDB接続層"""
import aioboto3
from botocore.config import Config

from app.core.config import settings


_dynamodb_client = None
_dynamodb_client_ctx = None
_dynamodb_resource = None
_dynamodb_resource_ctx = None


def get_table_name(table_suffix: str) -> str:
    """テーブル名を生成"""
    return f"{settings.dynamodb_table_prefix}{table_suffix}"


def _create_dynamodb_config() -> Config:
    """DynamoDB設定を作成"""
    return Config(
        region_name=settings.dynamodb_region,
        retries={"max_attempts": 3, "mode": "adaptive"},
    )


async def get_dynamodb_client():
    """DynamoDBクライアントを取得（シングルトン）"""
    global _dynamodb_client, _dynamodb_client_ctx
    
    if _dynamodb_client is None:
        session = aioboto3.Session()
        config = _create_dynamodb_config()
        
        context = session.client(
            "dynamodb",
            endpoint_url=settings.dynamodb_endpoint,
            config=config,
        )
        # aioboto3 の context manager を保持し、クライアントを取得
        _dynamodb_client_ctx = context
        _dynamodb_client = await context.__aenter__()
    
    return _dynamodb_client


async def get_dynamodb_resource():
    """DynamoDBリソースを取得（シングルトン）"""
    global _dynamodb_resource, _dynamodb_resource_ctx
    
    if _dynamodb_resource is None:
        session = aioboto3.Session()
        config = _create_dynamodb_config()
        
        context = session.resource(
            "dynamodb",
            endpoint_url=settings.dynamodb_endpoint,
            config=config,
        )
        # aioboto3 の context manager を保持し、リソースを取得
        _dynamodb_resource_ctx = context
        _dynamodb_resource = await context.__aenter__()
    
    return _dynamodb_resource


async def close_dynamodb():
    """DynamoDB接続を閉じる"""
    global _dynamodb_client, _dynamodb_client_ctx, _dynamodb_resource, _dynamodb_resource_ctx
    
    if _dynamodb_client_ctx is not None:
        await _dynamodb_client_ctx.__aexit__(None, None, None)
        _dynamodb_client_ctx = None
        _dynamodb_client = None
    
    if _dynamodb_resource_ctx is not None:
        await _dynamodb_resource_ctx.__aexit__(None, None, None)
        _dynamodb_resource_ctx = None
        _dynamodb_resource = None
