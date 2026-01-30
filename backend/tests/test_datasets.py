"""Datasets APIのテスト"""
import pytest
from fastapi import status
import boto3
import io
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.db.dynamodb import get_table_name
from app.db.s3 import get_bucket_name


@pytest.fixture
def sample_csv_content():
    """サンプルCSVコンテンツ"""
    df = pd.DataFrame({
        "col1": ["a", "b", "c"],
        "col2": [1, 2, 3],
    })
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue().encode("utf-8")




def test_list_datasets_success(test_client, setup_dynamodb_tables, sample_dataset, auth_headers):
    """Dataset一覧取得成功"""
    # Datasetを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Datasets"))
    table.put_item(Item=sample_dataset)
    
    # 一覧取得
    response = test_client.get("/api/datasets", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "pagination" in data




def test_create_dataset_from_csv_success(test_client, setup_dynamodb_tables, mock_s3, sample_csv_content, auth_headers):
    """CSVからDataset作成成功"""
    response = test_client.post(
        "/api/datasets",
        files={"file": ("test.csv", sample_csv_content, "text/csv")},
        data={
            "name": "Test Dataset",
            "encoding": "utf-8",
            "delimiter": ",",
            "has_header": True,
        },
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert data["data"]["name"] == "Test Dataset"
    assert data["data"]["row_count"] == 3
    assert data["data"]["column_count"] == 2




def test_create_dataset_from_csv_invalid(test_client, setup_dynamodb_tables, mock_s3, auth_headers):
    """CSVからDataset作成失敗（不正なCSV）"""
    invalid_csv = b"invalid,csv,content\n"
    response = test_client.post(
        "/api/datasets",
        files={"file": ("test.csv", invalid_csv, "text/csv")},
        data={
            "name": "Test Dataset",
            "encoding": "utf-8",
            "delimiter": ",",
            "has_header": True,
        },
        headers=auth_headers,
    )
    
    # CSVパースエラーは400を返す
    assert response.status_code == status.HTTP_400_BAD_REQUEST




def test_s3_import_dataset_success(test_client, setup_dynamodb_tables, mock_s3, sample_csv_content, auth_headers):
    """S3インポート成功"""
    # S3にCSVをアップロード
    s3_client = mock_s3
    s3_client.create_bucket(
        Bucket="test-bucket",
        CreateBucketConfiguration={"LocationConstraint": "ap-northeast-1"}
    )
    s3_client.put_object(
        Bucket="test-bucket",
        Key="test.csv",
        Body=sample_csv_content,
    )
    
    response = test_client.post(
        "/api/datasets/s3-import",
        json={
            "name": "S3 Dataset",
            "bucket": "test-bucket",
            "key": "test.csv",
            "encoding": "utf-8",
            "delimiter": ",",
            "has_header": True,
        },
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert data["data"]["name"] == "S3 Dataset"




def test_get_dataset_success(test_client, setup_dynamodb_tables, sample_dataset, auth_headers):
    """Dataset詳細取得成功"""
    # Datasetを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Datasets"))
    table.put_item(Item=sample_dataset)
    
    # 詳細取得
    response = test_client.get("/api/datasets/dataset_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["dataset_id"] == "dataset_test123"




def test_get_dataset_not_found(test_client, setup_dynamodb_tables, auth_headers):
    """Dataset詳細取得失敗（NotFound）"""
    response = test_client.get("/api/datasets/dataset_nonexistent", headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"




def test_update_dataset_success(test_client, setup_dynamodb_tables, sample_dataset, auth_headers):
    """Dataset更新成功"""
    # Datasetを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Datasets"))
    table.put_item(Item=sample_dataset)
    
    # 更新
    response = test_client.put(
        "/api/datasets/dataset_test123",
        json={"name": "Updated Dataset"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["name"] == "Updated Dataset"




def test_update_dataset_forbidden(test_client, setup_dynamodb_tables, sample_dataset, auth_headers):
    """Dataset更新失敗（権限なし）"""
    # 別ユーザのDatasetを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Datasets"))
    dataset = sample_dataset.copy()
    dataset["ownerId"] = "user_other"
    table.put_item(Item=dataset)
    
    # 更新（権限なし）
    response = test_client.put(
        "/api/datasets/dataset_test123",
        json={"name": "Updated Dataset"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "FORBIDDEN"




def test_delete_dataset_success(test_client, setup_dynamodb_tables, sample_dataset, auth_headers):
    """Dataset削除成功"""
    # Datasetを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Datasets"))
    table.put_item(Item=sample_dataset)
    
    # 削除
    response = test_client.delete("/api/datasets/dataset_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT




def test_delete_dataset_forbidden(test_client, setup_dynamodb_tables, sample_dataset, auth_headers):
    """Dataset削除失敗（権限なし）"""
    # 別ユーザのDatasetを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Datasets"))
    dataset = sample_dataset.copy()
    dataset["ownerId"] = "user_other"
    table.put_item(Item=dataset)
    
    # 削除（権限なし）
    response = test_client.delete("/api/datasets/dataset_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN




def test_get_dataset_preview_success(test_client, setup_dynamodb_tables, mock_s3, sample_dataset, auth_headers):
    """Datasetプレビュー取得成功"""
    # Datasetを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Datasets"))
    table.put_item(Item=sample_dataset)
    
    # ParquetファイルをS3にアップロード
    df = pd.DataFrame({"col1": ["a", "b"], "col2": [1, 2]})
    parquet_buffer = io.BytesIO()
    table = pa.Table.from_pandas(df)
    pq.write_table(table, parquet_buffer)
    parquet_buffer.seek(0)
    
    s3_client = mock_s3
    s3_client.put_object(
        Bucket=get_bucket_name("datasets"),
        Key="datasets/dataset_test123/data.parquet",
        Body=parquet_buffer.getvalue(),
    )
    
    # プレビュー取得
    response = test_client.get("/api/datasets/dataset_test123/preview", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "columns" in data["data"]
    assert "rows" in data["data"]
