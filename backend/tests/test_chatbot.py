"""Chatbot APIテスト"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.chatbot_service import (
    check_rate_limit,
    generate_dataset_summary,
    chat,
    RateLimitExceeded,
)


@pytest.fixture
def mock_dynamodb_client():
    """DynamoDBクライアントのモック"""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_s3_client():
    """S3クライアントのモック"""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_vertex_ai():
    """Vertex AIのモック"""
    with patch("app.services.chatbot_service.vertexai") as mock_vertexai:
        mock_model = MagicMock()
        mock_response = MagicMock()
        mock_response.text = "これはテスト回答です。"
        mock_model.generate_content.return_value = mock_response
        
        mock_generative_model = MagicMock(return_value=mock_model)
        
        with patch("app.services.chatbot_service.GenerativeModel", mock_generative_model):
            yield {
                "vertexai": mock_vertexai,
                "model": mock_model,
                "response": mock_response,
            }


@pytest.mark.asyncio
async def test_check_rate_limit_first_request(mock_dynamodb_client):
    """レート制限チェック - 初回リクエスト"""
    with patch("app.services.chatbot_service.get_dynamodb_client", return_value=mock_dynamodb_client):
        # 初回リクエスト（アイテムなし）
        mock_dynamodb_client.get_item.return_value = {}
        mock_dynamodb_client.put_item.return_value = {}
        
        # レート制限チェック（エラーなし）
        await check_rate_limit("user_123")
        
        assert mock_dynamodb_client.get_item.called
        assert mock_dynamodb_client.put_item.called


@pytest.mark.asyncio
async def test_check_rate_limit_within_limit(mock_dynamodb_client):
    """レート制限チェック - 制限内"""
    with patch("app.services.chatbot_service.get_dynamodb_client", return_value=mock_dynamodb_client):
        now = int(datetime.utcnow().timestamp())
        
        # 既存のリクエスト（5件）
        mock_dynamodb_client.get_item.return_value = {
            "Item": {
                "key": {"S": "chatbot_user_123"},
                "requests": {
                    "L": [
                        {"N": str(now - 50)},
                        {"N": str(now - 40)},
                        {"N": str(now - 30)},
                        {"N": str(now - 20)},
                        {"N": str(now - 10)},
                    ]
                },
            }
        }
        mock_dynamodb_client.put_item.return_value = {}
        
        # レート制限チェック（エラーなし）
        await check_rate_limit("user_123")
        
        assert mock_dynamodb_client.get_item.called
        assert mock_dynamodb_client.put_item.called


@pytest.mark.asyncio
async def test_check_rate_limit_exceeded(mock_dynamodb_client):
    """レート制限チェック - 制限超過"""
    with patch("app.services.chatbot_service.get_dynamodb_client", return_value=mock_dynamodb_client):
        now = int(datetime.utcnow().timestamp())
        
        # 既存のリクエスト（10件 = 上限）
        mock_dynamodb_client.get_item.return_value = {
            "Item": {
                "key": {"S": "chatbot_user_123"},
                "requests": {
                    "L": [{"N": str(now - i * 5)} for i in range(10)]
                },
            }
        }
        
        # レート制限超過エラー
        with pytest.raises(RateLimitExceeded):
            await check_rate_limit("user_123")


@pytest.mark.asyncio
async def test_generate_dataset_summary(mock_s3_client):
    """Datasetサマリ生成"""
    import io
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    
    # テストデータ
    df = pd.DataFrame({
        "id": [1, 2, 3, 4, 5],
        "name": ["Alice", "Bob", "Charlie", "David", "Eve"],
        "age": [25, 30, 35, 40, 45],
        "city": ["Tokyo", "Osaka", "Tokyo", "Kyoto", "Tokyo"],
    })
    
    # Parquetに変換
    table = pa.Table.from_pandas(df)
    parquet_buffer = io.BytesIO()
    pq.write_table(table, parquet_buffer)
    parquet_buffer.seek(0)
    
    # S3モック
    mock_response = MagicMock()
    mock_response["Body"].read = AsyncMock(return_value=parquet_buffer.getvalue())
    mock_s3_client.get_object.return_value = mock_response
    
    # Datasetモック
    mock_dataset = MagicMock()
    mock_dataset.name = "Test Dataset"
    mock_dataset.row_count = 5
    mock_dataset.column_count = 4
    mock_dataset.s3_path = "datasets/test/data.parquet"
    mock_dataset.schema = [
        MagicMock(name="id", dtype="int64", nullable=False),
        MagicMock(name="name", dtype="object", nullable=False),
        MagicMock(name="age", dtype="int64", nullable=False),
        MagicMock(name="city", dtype="object", nullable=False),
    ]
    
    with patch("app.services.chatbot_service.get_dataset", return_value=mock_dataset):
        with patch("app.services.chatbot_service.get_s3_client", return_value=mock_s3_client):
            with patch("app.services.chatbot_service.get_bucket_name", return_value="test-bucket"):
                summary = await generate_dataset_summary("dataset_123")
    
    # 検証
    assert summary["dataset_id"] == "dataset_123"
    assert summary["dataset_name"] == "Test Dataset"
    assert summary["row_count"] == 5
    assert summary["column_count"] == 4
    assert len(summary["schema"]) == 4
    assert len(summary["sample_rows"]) == 5
    assert "id" in summary["statistics"]
    assert "name" in summary["statistics"]
    assert summary["statistics"]["id"]["type"] == "numeric"
    assert summary["statistics"]["name"]["type"] == "categorical"


@pytest.mark.asyncio
async def test_chat_success(mock_vertex_ai, mock_dynamodb_client):
    """チャット - 成功"""
    # レート制限チェックをモック
    mock_dynamodb_client.get_item.return_value = {}
    mock_dynamodb_client.put_item.return_value = {}
    
    # get_referenced_datasetsをモック
    with patch("app.services.chatbot_service.get_referenced_datasets", return_value=["dataset_123"]):
        # generate_dataset_summaryをモック
        mock_summary = {
            "dataset_id": "dataset_123",
            "dataset_name": "Test Dataset",
            "row_count": 100,
            "column_count": 5,
            "schema": [],
            "sample_rows": [],
            "statistics": {},
        }
        with patch("app.services.chatbot_service.generate_dataset_summary", return_value=mock_summary):
            with patch("app.services.chatbot_service.get_dynamodb_client", return_value=mock_dynamodb_client):
                with patch("app.services.chatbot_service.settings") as mock_settings:
                    mock_settings.vertex_ai_project_id = "test-project"
                    mock_settings.vertex_ai_location = "asia-northeast1"
                    mock_settings.vertex_ai_model = "gemini-1.5-pro"
                    
                    result = await chat("dashboard_123", "データを要約して", "user_123")
    
    # 検証
    assert result["answer"] == "これはテスト回答です。"
    assert result["datasets_used"] == ["dataset_123"]
    assert mock_vertex_ai["vertexai"].init.called
    assert mock_vertex_ai["model"].generate_content.called


@pytest.mark.asyncio
async def test_chat_no_datasets(mock_dynamodb_client):
    """チャット - Datasetなし"""
    # レート制限チェックをモック
    mock_dynamodb_client.get_item.return_value = {}
    mock_dynamodb_client.put_item.return_value = {}
    
    # get_referenced_datasetsをモック（空リスト）
    with patch("app.services.chatbot_service.get_referenced_datasets", return_value=[]):
        with patch("app.services.chatbot_service.get_dynamodb_client", return_value=mock_dynamodb_client):
            result = await chat("dashboard_123", "データを要約して", "user_123")
    
    # 検証
    assert "関連付けられていません" in result["answer"]
    assert result["datasets_used"] == []


@pytest.mark.asyncio
async def test_chat_vertex_ai_not_configured(mock_dynamodb_client):
    """チャット - Vertex AI未設定"""
    # レート制限チェックをモック
    mock_dynamodb_client.get_item.return_value = {}
    mock_dynamodb_client.put_item.return_value = {}
    
    # get_referenced_datasetsをモック
    with patch("app.services.chatbot_service.get_referenced_datasets", return_value=["dataset_123"]):
        # generate_dataset_summaryをモック
        mock_summary = {
            "dataset_id": "dataset_123",
            "dataset_name": "Test Dataset",
            "row_count": 100,
            "column_count": 5,
            "schema": [],
            "sample_rows": [],
            "statistics": {},
        }
        with patch("app.services.chatbot_service.generate_dataset_summary", return_value=mock_summary):
            with patch("app.services.chatbot_service.get_dynamodb_client", return_value=mock_dynamodb_client):
                with patch("app.services.chatbot_service.settings") as mock_settings:
                    mock_settings.vertex_ai_project_id = None
                    
                    result = await chat("dashboard_123", "データを要約して", "user_123")
    
    # 検証
    assert "設定されていません" in result["answer"]
    assert result["datasets_used"] == ["dataset_123"]
