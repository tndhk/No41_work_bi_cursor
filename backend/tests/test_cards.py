"""Cards APIのテスト"""
import pytest
from fastapi import status
import boto3

from app.db.dynamodb import get_table_name




def test_list_cards_success(test_client, setup_dynamodb_tables, sample_card, auth_headers):
    """Card一覧取得成功"""
    # Cardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Cards"))
    table.put_item(Item=sample_card)
    
    # 一覧取得
    response = test_client.get("/api/cards", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "pagination" in data




def test_create_card_success(test_client, setup_dynamodb_tables, sample_dataset, auth_headers):
    """Card作成成功"""
    # Datasetを作成（Card作成に必要）
    dynamodb = setup_dynamodb_tables
    datasets_table = dynamodb.Table(get_table_name("Datasets"))
    datasets_table.put_item(Item=sample_dataset)
    
    # Card作成
    response = test_client.post(
        "/api/cards",
        json={
            "name": "Test Card",
            "dataset_id": "dataset_test123",
            "code": "def render(dataset, filters, params):\n    return {'html': '<div>Test</div>', 'used_columns': [], 'filter_applicable': []}",
            "params": {},
            "used_columns": [],
            "filter_applicable": [],
        },
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert data["data"]["name"] == "Test Card"




def test_create_card_dataset_not_found(test_client, setup_dynamodb_tables, auth_headers):
    """Card作成失敗（Dataset不存在）"""
    response = test_client.post(
        "/api/cards",
        json={
            "name": "Test Card",
            "dataset_id": "dataset_nonexistent",
            "code": "def render(dataset, filters, params):\n    return {'html': '<div>Test</div>', 'used_columns': [], 'filter_applicable': []}",
        },
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"




def test_get_card_success(test_client, setup_dynamodb_tables, sample_card, auth_headers):
    """Card詳細取得成功"""
    # Cardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Cards"))
    table.put_item(Item=sample_card)
    
    # 詳細取得
    response = test_client.get("/api/cards/card_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["card_id"] == "card_test123"




def test_get_card_not_found(test_client, setup_dynamodb_tables, auth_headers):
    """Card詳細取得失敗（NotFound）"""
    response = test_client.get("/api/cards/card_nonexistent", headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND




def test_update_card_success(test_client, setup_dynamodb_tables, sample_card, sample_dataset, auth_headers):
    """Card更新成功"""
    # CardとDatasetを作成
    dynamodb = setup_dynamodb_tables
    cards_table = dynamodb.Table(get_table_name("Cards"))
    datasets_table = dynamodb.Table(get_table_name("Datasets"))
    cards_table.put_item(Item=sample_card)
    datasets_table.put_item(Item=sample_dataset)
    
    # 更新
    response = test_client.put(
        "/api/cards/card_test123",
        json={"name": "Updated Card"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["name"] == "Updated Card"




def test_update_card_forbidden(test_client, setup_dynamodb_tables, sample_card, auth_headers):
    """Card更新失敗（権限なし）"""
    # 別ユーザのCardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Cards"))
    card = sample_card.copy()
    card["ownerId"] = "user_other"
    table.put_item(Item=card)
    
    # 更新（権限なし）
    response = test_client.put(
        "/api/cards/card_test123",
        json={"name": "Updated Card"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN




def test_delete_card_success(test_client, setup_dynamodb_tables, sample_card, auth_headers):
    """Card削除成功"""
    # Cardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Cards"))
    table.put_item(Item=sample_card)
    
    # 削除
    response = test_client.delete("/api/cards/card_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT




def test_preview_card_not_implemented(test_client, setup_dynamodb_tables, sample_card, auth_headers):
    """Cardプレビュー実行（未実装）"""
    # Cardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Cards"))
    table.put_item(Item=sample_card)
    
    # プレビュー実行
    response = test_client.post(
        "/api/cards/card_test123/preview",
        json={"filters": {}, "params": {}},
        headers=auth_headers,
    )
    
    # Executor未実装のため500エラー
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
