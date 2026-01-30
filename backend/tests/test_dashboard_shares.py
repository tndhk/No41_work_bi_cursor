"""Dashboard Shares APIのテスト"""
import pytest
from fastapi import status
import boto3
from datetime import datetime

from app.db.dynamodb import get_table_name


@pytest.fixture
def sample_share():
    """テスト用Shareデータ"""
    return {
        "shareId": "share_test123",
        "dashboardId": "dashboard_test123",
        "sharedToType": "user",
        "sharedToId": "user_shared",
        "permission": "viewer",
        "sharedBy": "user_test123",
        "createdAt": int(datetime.utcnow().timestamp()),
    }




def test_list_shares_success(test_client, setup_dynamodb_tables, sample_dashboard, sample_share, auth_headers):
    """共有一覧取得成功"""
    # DashboardとShareを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    shares_table = dynamodb.Table(get_table_name("DashboardShares"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    shares_table.put_item(Item=sample_share)
    
    # 共有一覧取得
    response = test_client.get("/api/dashboards/dashboard_test123/shares", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0




def test_list_shares_forbidden(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """共有一覧取得失敗（権限なし）"""
    # 別ユーザのDashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    dashboard = sample_dashboard.copy()
    dashboard["ownerId"] = "user_other"
    table.put_item(Item=dashboard)
    
    # 共有一覧取得（権限なし）
    response = test_client.get("/api/dashboards/dashboard_test123/shares", headers=auth_headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN




def test_create_share_success(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """共有追加成功"""
    # Dashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    table.put_item(Item=sample_dashboard)
    
    # 共有追加
    response = test_client.post(
        "/api/dashboards/dashboard_test123/shares",
        json={
            "shared_to_type": "user",
            "shared_to_id": "user_shared",
            "permission": "viewer",
        },
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert data["data"]["permission"] == "viewer"




def test_create_share_forbidden(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """共有追加失敗（権限なし）"""
    # 別ユーザのDashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    dashboard = sample_dashboard.copy()
    dashboard["ownerId"] = "user_other"
    table.put_item(Item=dashboard)
    
    # 共有追加（権限なし）
    response = test_client.post(
        "/api/dashboards/dashboard_test123/shares",
        json={
            "shared_to_type": "user",
            "shared_to_id": "user_shared",
            "permission": "viewer",
        },
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN




def test_update_share_success(test_client, setup_dynamodb_tables, sample_dashboard, sample_share, auth_headers):
    """共有更新成功"""
    # DashboardとShareを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    shares_table = dynamodb.Table(get_table_name("DashboardShares"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    shares_table.put_item(Item=sample_share)
    
    # 共有更新
    response = test_client.put(
        "/api/dashboards/dashboard_test123/shares/share_test123",
        json={"permission": "editor"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["permission"] == "editor"




def test_delete_share_success(test_client, setup_dynamodb_tables, sample_dashboard, sample_share, auth_headers):
    """共有削除成功"""
    # DashboardとShareを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    shares_table = dynamodb.Table(get_table_name("DashboardShares"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    shares_table.put_item(Item=sample_share)
    
    # 共有削除
    response = test_client.delete("/api/dashboards/dashboard_test123/shares/share_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
