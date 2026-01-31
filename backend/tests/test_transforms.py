"""Transforms APIのテスト - TDD"""
import pytest
from fastapi import status
import boto3

from app.db.dynamodb import get_table_name




def test_list_transforms_success(test_client, setup_dynamodb_tables, sample_transform, auth_headers):
    """Transform一覧取得成功"""
    # Transformを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Transforms"))
    table.put_item(Item=sample_transform)
    
    # 一覧取得
    response = test_client.get("/api/transforms", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) == 1
    assert data["data"][0]["transform_id"] == "transform_test123"




def test_create_transform_success(test_client, setup_dynamodb_tables, sample_dataset, auth_headers):
    """Transform作成成功"""
    # Datasetを作成（Transform作成に必要）
    dynamodb = setup_dynamodb_tables
    datasets_table = dynamodb.Table(get_table_name("Datasets"))
    datasets_table.put_item(Item=sample_dataset)
    
    # Transform作成
    response = test_client.post(
        "/api/transforms",
        json={
            "name": "Test Transform",
            "code": "def transform(input_datasets, params):\n    return input_datasets[0]",
            "input_dataset_ids": ["dataset_test123"],
            "params": {},
            "schedule": None,
        },
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert data["data"]["name"] == "Test Transform"
    assert "transform_id" in data["data"]




def test_get_transform_success(test_client, setup_dynamodb_tables, sample_transform, auth_headers):
    """Transform詳細取得成功"""
    # Transformを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Transforms"))
    table.put_item(Item=sample_transform)
    
    # 詳細取得
    response = test_client.get("/api/transforms/transform_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["transform_id"] == "transform_test123"




def test_update_transform_success(test_client, setup_dynamodb_tables, sample_transform, sample_dataset, auth_headers):
    """Transform更新成功"""
    # TransformとDatasetを作成
    dynamodb = setup_dynamodb_tables
    transforms_table = dynamodb.Table(get_table_name("Transforms"))
    datasets_table = dynamodb.Table(get_table_name("Datasets"))
    transforms_table.put_item(Item=sample_transform)
    datasets_table.put_item(Item=sample_dataset)
    
    # 更新
    response = test_client.put(
        "/api/transforms/transform_test123",
        json={"name": "Updated Transform"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["name"] == "Updated Transform"




def test_delete_transform_success(test_client, setup_dynamodb_tables, sample_transform, auth_headers):
    """Transform削除成功"""
    # Transformを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Transforms"))
    table.put_item(Item=sample_transform)
    
    # 削除
    response = test_client.delete("/api/transforms/transform_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT




def test_execute_transform_not_implemented(test_client, setup_dynamodb_tables, sample_transform, auth_headers):
    """Transform実行（未実装）"""
    # Transformを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Transforms"))
    table.put_item(Item=sample_transform)
    
    # 実行
    response = test_client.post(
        "/api/transforms/transform_test123/execute",
        headers=auth_headers,
    )
    
    # Executor未実装のため500エラー
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "EXECUTION_ERROR"




def test_list_executions_success(test_client, setup_dynamodb_tables, sample_transform, auth_headers):
    """Transform実行履歴取得成功"""
    # Transformを作成
    dynamodb = setup_dynamodb_tables
    transforms_table = dynamodb.Table(get_table_name("Transforms"))
    transforms_table.put_item(Item=sample_transform)
    
    # 実行履歴を取得
    response = test_client.get(
        "/api/transforms/transform_test123/executions",
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "pagination" in data
