"""DynamoDB接続層のテスト"""
import pytest
from moto import mock_dynamodb
import boto3
from datetime import datetime

from app.db.dynamodb import get_dynamodb_client, get_table_name


@pytest.fixture
def dynamodb_mock():
    """DynamoDBモック"""
    with mock_dynamodb():
        yield boto3.resource("dynamodb", region_name="ap-northeast-1")


@pytest.mark.asyncio
async def test_get_dynamodb_client():
    """DynamoDBクライアントを取得できる"""
    client = await get_dynamodb_client()
    assert client is not None


def test_get_table_name():
    """テーブル名を正しく生成する"""
    table_name = get_table_name("Users")
    assert table_name == "bi_Users"


def test_get_table_name_with_custom_prefix():
    """カスタムプレフィックスでテーブル名を生成する"""
    import os
    original = os.environ.get("DYNAMODB_TABLE_PREFIX")
    os.environ["DYNAMODB_TABLE_PREFIX"] = "custom_"
    
    try:
        from app.db.dynamodb import get_table_name
        table_name = get_table_name("Users")
        assert table_name == "custom_Users"
    finally:
        if original:
            os.environ["DYNAMODB_TABLE_PREFIX"] = original
        else:
            os.environ.pop("DYNAMODB_TABLE_PREFIX", None)
