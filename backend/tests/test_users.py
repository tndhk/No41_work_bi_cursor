"""Users APIのテスト"""
import pytest
from fastapi import status
import boto3

from app.core.security import hash_password
from app.db.dynamodb import get_table_name




def test_list_users_success(test_client, setup_dynamodb_tables, sample_user, auth_headers):
    """ユーザ一覧取得成功"""
    # ユーザを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Users"))
    table.put_item(Item=sample_user)
    
    # 一覧取得
    response = test_client.get("/api/users", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) > 0




def test_list_users_with_query(test_client, setup_dynamodb_tables, sample_user, auth_headers):
    """ユーザ一覧取得（検索クエリ付き）"""
    # ユーザを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Users"))
    table.put_item(Item=sample_user)
    
    # 検索
    response = test_client.get("/api/users?q=Test", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data




def test_get_user_success(test_client, setup_dynamodb_tables, sample_user, auth_headers):
    """ユーザ詳細取得成功"""
    # ユーザを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Users"))
    table.put_item(Item=sample_user)
    
    # 詳細取得
    response = test_client.get("/api/users/user_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["user_id"] == "user_test123"
    assert data["data"]["email"] == "test@example.com"




def test_get_user_not_found(test_client, setup_dynamodb_tables, auth_headers):
    """ユーザ詳細取得失敗（NotFound）"""
    response = test_client.get("/api/users/user_nonexistent", headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"
