"""FilterViews APIのテスト"""
import pytest
from fastapi import status
import boto3
from datetime import datetime

from app.db.dynamodb import get_table_name


@pytest.fixture
def sample_filter_view():
    """テスト用FilterViewデータ"""
    now = int(datetime.utcnow().timestamp())
    return {
        "filterViewId": "filterview_test123",
        "dashboardId": "dashboard_test123",
        "name": "Test FilterView",
        "ownerId": "user_test123",
        "filterState": {"category": "test"},
        "isShared": False,
        "isDefault": False,
        "createdAt": now,
        "updatedAt": now,
    }




def test_list_filter_views_success(test_client, setup_dynamodb_tables, sample_dashboard, sample_filter_view, auth_headers):
    """FilterView一覧取得成功"""
    # DashboardとFilterViewを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    filter_views_table = dynamodb.Table(get_table_name("FilterViews"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    filter_views_table.put_item(Item=sample_filter_view)
    
    # 一覧取得
    response = test_client.get("/api/dashboards/dashboard_test123/filter-views", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data




def test_list_filter_views_forbidden(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """FilterView一覧取得失敗（権限なし）"""
    # 別ユーザのDashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    dashboard = sample_dashboard.copy()
    dashboard["ownerId"] = "user_other"
    table.put_item(Item=dashboard)
    
    # 一覧取得（権限なし）
    response = test_client.get("/api/dashboards/dashboard_test123/filter-views", headers=auth_headers)
    
    assert response.status_code == status.HTTP_403_FORBIDDEN




def test_create_filter_view_success(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """FilterView作成成功"""
    # Dashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    table.put_item(Item=sample_dashboard)
    
    # FilterView作成
    response = test_client.post(
        "/api/dashboards/dashboard_test123/filter-views",
        json={
            "name": "New FilterView",
            "filter_state": {"category": "test"},
            "is_shared": False,
            "is_default": False,
        },
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert data["data"]["name"] == "New FilterView"




def test_create_filter_view_forbidden(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """FilterView作成失敗（権限なし）"""
    # 別ユーザのDashboardを作成（共有なし）
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    dashboard = sample_dashboard.copy()
    dashboard["ownerId"] = "user_other"
    table.put_item(Item=dashboard)
    
    # FilterView作成（権限なし）
    response = test_client.post(
        "/api/dashboards/dashboard_test123/filter-views",
        json={
            "name": "New FilterView",
            "filter_state": {"category": "test"},
        },
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN




def test_get_filter_view_success(test_client, setup_dynamodb_tables, sample_dashboard, sample_filter_view, auth_headers):
    """FilterView詳細取得成功"""
    # DashboardとFilterViewを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    filter_views_table = dynamodb.Table(get_table_name("FilterViews"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    filter_views_table.put_item(Item=sample_filter_view)
    
    # 詳細取得
    response = test_client.get("/api/dashboards/dashboard_test123/filter-views/filterview_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["filter_view_id"] == "filterview_test123"




def test_get_filter_view_not_found(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """FilterView詳細取得失敗（NotFound）"""
    # Dashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    table.put_item(Item=sample_dashboard)
    
    # 詳細取得
    response = test_client.get("/api/dashboards/dashboard_test123/filter-views/filterview_nonexistent", headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND




def test_update_filter_view_success(test_client, setup_dynamodb_tables, sample_dashboard, sample_filter_view, auth_headers):
    """FilterView更新成功"""
    # DashboardとFilterViewを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    filter_views_table = dynamodb.Table(get_table_name("FilterViews"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    filter_views_table.put_item(Item=sample_filter_view)
    
    # 更新
    response = test_client.put(
        "/api/dashboards/dashboard_test123/filter-views/filterview_test123",
        json={"name": "Updated FilterView"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["name"] == "Updated FilterView"




def test_update_filter_view_forbidden(test_client, setup_dynamodb_tables, sample_dashboard, sample_filter_view, auth_headers):
    """FilterView更新失敗（権限なし）"""
    # Dashboardと別ユーザのFilterViewを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    filter_views_table = dynamodb.Table(get_table_name("FilterViews"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    filter_view = sample_filter_view.copy()
    filter_view["ownerId"] = "user_other"
    filter_views_table.put_item(Item=filter_view)
    
    # 更新（権限なし）
    response = test_client.put(
        "/api/dashboards/dashboard_test123/filter-views/filterview_test123",
        json={"name": "Updated FilterView"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN




def test_delete_filter_view_success(test_client, setup_dynamodb_tables, sample_dashboard, sample_filter_view, auth_headers):
    """FilterView削除成功"""
    # DashboardとFilterViewを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    filter_views_table = dynamodb.Table(get_table_name("FilterViews"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    filter_views_table.put_item(Item=sample_filter_view)
    
    # 削除
    response = test_client.delete("/api/dashboards/dashboard_test123/filter-views/filterview_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
