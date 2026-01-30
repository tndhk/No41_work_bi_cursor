"""認証APIのテスト"""
import pytest
from fastapi import status
import boto3

from app.core.security import hash_password
from app.db.dynamodb import get_table_name



def test_login_success(test_client, setup_dynamodb_tables, sample_user):
    """ログイン成功"""
    # ユーザを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Users"))
    table.put_item(Item=sample_user)
    
    # ログイン
    response = test_client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
        },
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "test@example.com"



def test_login_failure_invalid_email(test_client, setup_dynamodb_tables):
    """ログイン失敗（メールアドレス不正）"""
    response = test_client.post(
        "/api/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "testpassword123",
        },
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"



def test_login_failure_invalid_password(test_client, setup_dynamodb_tables, sample_user):
    """ログイン失敗（パスワード不正）"""
    # ユーザを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Users"))
    table.put_item(Item=sample_user)
    
    # ログイン
    response = test_client.post(
        "/api/auth/login",
        json={
            "email": "test@example.com",
            "password": "wrongpassword",
        },
    )
    
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "UNAUTHORIZED"



def test_get_me_success(test_client, setup_dynamodb_tables, sample_user, auth_headers):
    """me取得成功"""
    # ユーザを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Users"))
    table.put_item(Item=sample_user)
    
    # me取得
    response = test_client.get("/api/auth/me", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["user_id"] == "user_test123"
    assert data["email"] == "test@example.com"



def test_get_me_failure_unauthorized(test_client):
    """me取得失敗（未認証）"""
    response = test_client.get("/api/auth/me")
    
    assert response.status_code == status.HTTP_403_FORBIDDEN



def test_logout_success(test_client, auth_headers):
    """ログアウト成功"""
    response = test_client.post("/api/auth/logout", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data
