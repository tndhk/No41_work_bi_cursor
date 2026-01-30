"""共有テストフィクスチャ"""
import pytest
from moto import mock_aws
import boto3
from datetime import datetime
from fastapi.testclient import TestClient
from botocore.exceptions import ClientError
from unittest.mock import patch

from app.main import app
from app.core.security import create_access_token
from app.db.dynamodb import get_table_name


def _hash_password_for_test(password: str) -> str:
    """テスト用のパスワードハッシュ（bcrypt を直接使用）"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


class AsyncClientWrapper:
    """boto3 同期クライアントを非同期風にラップ"""
    def __init__(self, sync_client):
        self._sync_client = sync_client
    
    def __getattr__(self, name):
        attr = getattr(self._sync_client, name)
        if callable(attr):
            async def async_wrapper(*args, **kwargs):
                result = attr(*args, **kwargs)
                if isinstance(result, dict) and "Body" in result and hasattr(result["Body"], "read"):
                    result = dict(result)
                    result["Body"] = AsyncBodyWrapper(result["Body"])
                return result
            return async_wrapper
        return attr


class AsyncBodyWrapper:
    """boto3 StreamingBody を非同期読み取り対応にラップ"""
    def __init__(self, body):
        self._body = body
    
    async def read(self, *args, **kwargs):
        return self._body.read(*args, **kwargs)


class AsyncResourceWrapper:
    """boto3 同期リソースを非同期風にラップ"""
    def __init__(self, sync_resource):
        self._sync_resource = sync_resource
    
    def __getattr__(self, name):
        return getattr(self._sync_resource, name)


@pytest.fixture
def test_client():
    """FastAPI TestClient"""
    return TestClient(app)


# パッチ対象のサービスモジュール一覧
DYNAMODB_PATCH_TARGETS = [
    "app.services.user_service.get_dynamodb_client",
    "app.services.group_service.get_dynamodb_client",
    "app.services.dataset_service.get_dynamodb_client",
    "app.services.card_service.get_dynamodb_client",
    "app.services.dashboard_service.get_dynamodb_client",
    "app.services.dashboard_share_service.get_dynamodb_client",
    "app.services.filter_view_service.get_dynamodb_client",
]

S3_PATCH_TARGETS = [
    "app.services.dataset_service.get_s3_client",
]


@pytest.fixture
def mock_aws_context():
    """AWS モック（moto）のコンテキスト - 全サービスで共有"""
    with mock_aws():
        # DynamoDB
        ddb_sync_client = boto3.client("dynamodb", region_name="ap-northeast-1")
        ddb_sync_resource = boto3.resource("dynamodb", region_name="ap-northeast-1")
        ddb_async_client = AsyncClientWrapper(ddb_sync_client)
        ddb_async_resource = AsyncResourceWrapper(ddb_sync_resource)
        
        async def mock_get_ddb_client():
            return ddb_async_client
        
        async def mock_get_ddb_resource():
            return ddb_async_resource
        
        # S3
        s3_sync_client = boto3.client("s3", region_name="ap-northeast-1")
        s3_sync_client.create_bucket(
            Bucket="bi-datasets",
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"}
        )
        s3_sync_client.create_bucket(
            Bucket="bi-static",
            CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"}
        )
        s3_async_client = AsyncClientWrapper(s3_sync_client)
        
        async def mock_get_s3_client():
            return s3_async_client
        
        # すべてのパッチを適用
        patches = []
        for target in DYNAMODB_PATCH_TARGETS:
            p = patch(target, mock_get_ddb_client)
            patches.append(p)
            p.start()
        
        for target in S3_PATCH_TARGETS:
            p = patch(target, mock_get_s3_client)
            patches.append(p)
            p.start()
        
        try:
            yield {
                "dynamodb_resource": ddb_sync_resource,
                "dynamodb_client": ddb_sync_client,
                "s3_client": s3_sync_client,
            }
        finally:
            for p in patches:
                p.stop()


@pytest.fixture
def mock_dynamodb(mock_aws_context):
    """DynamoDBモック（後方互換性のため）"""
    return mock_aws_context["dynamodb_resource"]


@pytest.fixture
def mock_s3(mock_aws_context):
    """S3モック（後方互換性のため）"""
    return mock_aws_context["s3_client"]


@pytest.fixture
def auth_headers():
    """認証済みヘッダー（JWT付き）"""
    user_id = "user_test123"
    token = create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def sample_user():
    """テスト用ユーザデータ"""
    return {
        "userId": "user_test123",
        "email": "test@example.com",
        "name": "Test User",
        "passwordHash": _hash_password_for_test("testpassword123"),
        "createdAt": int(datetime.utcnow().timestamp()),
        "updatedAt": int(datetime.utcnow().timestamp()),
    }


@pytest.fixture
def sample_group():
    """テスト用グループデータ"""
    return {
        "groupId": "group_test123",
        "name": "Test Group",
        "createdAt": int(datetime.utcnow().timestamp()),
        "updatedAt": int(datetime.utcnow().timestamp()),
    }


@pytest.fixture
def sample_dataset():
    """テスト用Datasetデータ"""
    now = int(datetime.utcnow().timestamp())
    return {
        "datasetId": "dataset_test123",
        "name": "Test Dataset",
        "ownerId": "user_test123",
        "sourceType": "local_csv",
        "sourceConfig": {
            "encoding": "utf-8",
            "delimiter": ",",
            "has_header": True,
        },
        "schema": [
            {"name": "col1", "dtype": "object", "nullable": False},
            {"name": "col2", "dtype": "int64", "nullable": True},
        ],
        "rowCount": 100,
        "columnCount": 2,
        "s3Path": "datasets/dataset_test123/data.parquet",
        "createdAt": now,
        "updatedAt": now,
        "lastImportAt": now,
        "lastImportBy": "user_test123",
    }


@pytest.fixture
def sample_card():
    """テスト用Cardデータ"""
    now = int(datetime.utcnow().timestamp())
    return {
        "cardId": "card_test123",
        "name": "Test Card",
        "ownerId": "user_test123",
        "datasetId": "dataset_test123",
        "code": "def render(dataset, filters, params):\n    return {'html': '<div>Test</div>', 'used_columns': [], 'filter_applicable': []}",
        "params": {},
        "usedColumns": [],
        "filterApplicable": [],
        "createdAt": now,
        "updatedAt": now,
    }


@pytest.fixture
def sample_dashboard():
    """テスト用Dashboardデータ"""
    now = int(datetime.utcnow().timestamp())
    return {
        "dashboardId": "dashboard_test123",
        "name": "Test Dashboard",
        "ownerId": "user_test123",
        "layout": {"cards": []},
        "filters": [],
        "createdAt": now,
        "updatedAt": now,
    }


def _ensure_table_exists(client, table_name, create_params):
    """テーブルが存在しない場合のみ作成（存在する場合はそのまま）"""
    try:
        client.describe_table(TableName=table_name)
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            client.create_table(**create_params)
        else:
            raise


@pytest.fixture
def setup_dynamodb_tables(mock_dynamodb):
    """DynamoDBテーブルをセットアップ"""
    dynamodb = mock_dynamodb
    # boto3 クライアントを直接取得（moto のコンテキスト内）
    client = boto3.client("dynamodb", region_name="ap-northeast-1")
    
    table_definitions = [
        {
            "TableName": get_table_name("Users"),
            "KeySchema": [{"AttributeName": "userId", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "userId", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": get_table_name("Groups"),
            "KeySchema": [{"AttributeName": "groupId", "KeyType": "HASH"}],
            "AttributeDefinitions": [{"AttributeName": "groupId", "AttributeType": "S"}],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": get_table_name("GroupMembers"),
            "KeySchema": [
                {"AttributeName": "groupId", "KeyType": "HASH"},
                {"AttributeName": "userId", "KeyType": "RANGE"},
            ],
            "AttributeDefinitions": [
                {"AttributeName": "groupId", "AttributeType": "S"},
                {"AttributeName": "userId", "AttributeType": "S"},
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": get_table_name("Datasets"),
            "KeySchema": [{"AttributeName": "datasetId", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "datasetId", "AttributeType": "S"},
                {"AttributeName": "ownerId", "AttributeType": "S"},
                {"AttributeName": "createdAt", "AttributeType": "N"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "DatasetsByOwner",
                    "KeySchema": [
                        {"AttributeName": "ownerId", "KeyType": "HASH"},
                        {"AttributeName": "createdAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": get_table_name("Cards"),
            "KeySchema": [{"AttributeName": "cardId", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "cardId", "AttributeType": "S"},
                {"AttributeName": "ownerId", "AttributeType": "S"},
                {"AttributeName": "createdAt", "AttributeType": "N"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "CardsByOwner",
                    "KeySchema": [
                        {"AttributeName": "ownerId", "KeyType": "HASH"},
                        {"AttributeName": "createdAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": get_table_name("Dashboards"),
            "KeySchema": [{"AttributeName": "dashboardId", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "dashboardId", "AttributeType": "S"},
                {"AttributeName": "ownerId", "AttributeType": "S"},
                {"AttributeName": "createdAt", "AttributeType": "N"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "DashboardsByOwner",
                    "KeySchema": [
                        {"AttributeName": "ownerId", "KeyType": "HASH"},
                        {"AttributeName": "createdAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": get_table_name("DashboardShares"),
            "KeySchema": [{"AttributeName": "shareId", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "shareId", "AttributeType": "S"},
                {"AttributeName": "dashboardId", "AttributeType": "S"},
                {"AttributeName": "createdAt", "AttributeType": "N"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "SharesByDashboard",
                    "KeySchema": [
                        {"AttributeName": "dashboardId", "KeyType": "HASH"},
                        {"AttributeName": "createdAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
        {
            "TableName": get_table_name("FilterViews"),
            "KeySchema": [{"AttributeName": "filterViewId", "KeyType": "HASH"}],
            "AttributeDefinitions": [
                {"AttributeName": "filterViewId", "AttributeType": "S"},
                {"AttributeName": "dashboardId", "AttributeType": "S"},
                {"AttributeName": "createdAt", "AttributeType": "N"},
            ],
            "GlobalSecondaryIndexes": [
                {
                    "IndexName": "FilterViewsByDashboard",
                    "KeySchema": [
                        {"AttributeName": "dashboardId", "KeyType": "HASH"},
                        {"AttributeName": "createdAt", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ],
            "BillingMode": "PAY_PER_REQUEST",
        },
    ]
    
    for table_def in table_definitions:
        _ensure_table_exists(client, table_def["TableName"], table_def)
    
    yield dynamodb
