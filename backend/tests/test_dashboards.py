"""Dashboards APIのテスト"""
import pytest
from fastapi import status
import boto3

from app.db.dynamodb import get_table_name




def test_list_dashboards_success(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """Dashboard一覧取得成功"""
    # Dashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    table.put_item(Item=sample_dashboard)
    
    # 一覧取得
    response = test_client.get("/api/dashboards", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "pagination" in data




def test_create_dashboard_success(test_client, setup_dynamodb_tables, auth_headers):
    """Dashboard作成成功"""
    response = test_client.post(
        "/api/dashboards",
        json={
            "name": "New Dashboard",
            "layout": {},
            "filters": [],
        },
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert data["data"]["name"] == "New Dashboard"




def test_get_dashboard_success(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """Dashboard詳細取得成功"""
    # Dashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    table.put_item(Item=sample_dashboard)
    
    # 詳細取得
    response = test_client.get("/api/dashboards/dashboard_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["dashboard_id"] == "dashboard_test123"
    assert "permission" in data




def test_get_dashboard_not_found(test_client, setup_dynamodb_tables, auth_headers):
    """Dashboard詳細取得失敗（NotFound）"""
    response = test_client.get("/api/dashboards/dashboard_nonexistent", headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND




def test_get_dashboard_forbidden(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """Dashboard詳細取得失敗（権限なし）"""
    # 別ユーザのDashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    dashboard = sample_dashboard.copy()
    dashboard["ownerId"] = "user_other"
    table.put_item(Item=dashboard)
    
    # 詳細取得（権限なし）
    response = test_client.get("/api/dashboards/dashboard_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN




def test_update_dashboard_success(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """Dashboard更新成功"""
    # Dashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    table.put_item(Item=sample_dashboard)
    
    # 更新
    response = test_client.put(
        "/api/dashboards/dashboard_test123",
        json={"name": "Updated Dashboard"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["name"] == "Updated Dashboard"




def test_update_dashboard_forbidden(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """Dashboard更新失敗（権限なし）"""
    # 別ユーザのDashboardを作成（共有なし）
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    dashboard = sample_dashboard.copy()
    dashboard["ownerId"] = "user_other"
    table.put_item(Item=dashboard)
    
    # 更新（権限なし）
    response = test_client.put(
        "/api/dashboards/dashboard_test123",
        json={"name": "Updated Dashboard"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN




def test_delete_dashboard_success(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """Dashboard削除成功"""
    # Dashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    table.put_item(Item=sample_dashboard)
    
    # 削除
    response = test_client.delete("/api/dashboards/dashboard_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT




def test_delete_dashboard_forbidden(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """Dashboard削除失敗（権限なし）"""
    # 別ユーザのDashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    dashboard = sample_dashboard.copy()
    dashboard["ownerId"] = "user_other"
    table.put_item(Item=dashboard)
    
    # 削除（権限なし）
    response = test_client.delete("/api/dashboards/dashboard_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN




def test_clone_dashboard_success(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """Dashboard複製成功"""
    # Dashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    table.put_item(Item=sample_dashboard)
    
    # 複製
    response = test_client.post(
        "/api/dashboards/dashboard_test123/clone",
        json={"name": "Cloned Dashboard"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert data["data"]["name"] == "Cloned Dashboard"




def test_get_referenced_datasets_success(test_client, setup_dynamodb_tables, sample_dashboard, sample_card, auth_headers):
    """参照Dataset一覧取得成功"""
    # DashboardとCardを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    cards_table = dynamodb.Table(get_table_name("Cards"))
    
    dashboard = sample_dashboard.copy()
    dashboard["layout"] = {
        "M": {
            "cards": {
                "L": [
                    {
                        "M": {
                            "cardId": {"S": "card_test123"}
                        }
                    }
                ]
            }
        }
    }
    dashboards_table.put_item(Item=dashboard)
    cards_table.put_item(Item=sample_card)
    
    # 参照Dataset一覧取得
    response = test_client.get("/api/dashboards/dashboard_test123/referenced-datasets", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert isinstance(data["data"], list)
