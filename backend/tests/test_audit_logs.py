"""Audit Logs APIのテスト"""
import pytest
from fastapi import status
import boto3
from datetime import datetime, timedelta

from app.db.dynamodb import get_table_name


@pytest.fixture
def sample_audit_log():
    """テスト用AuditLogデータ（DynamoDB形式）"""
    now = int(datetime.utcnow().timestamp() * 1000)
    return {
        "logId": {"S": "log_test123"},
        "timestamp": {"N": str(now)},
        "eventType": {"S": "DASHBOARD_SHARE_ADDED"},
        "userId": {"S": "user_test123"},
        "targetType": {"S": "Dashboard"},
        "targetId": {"S": "dashboard_test123"},
        "details": {
            "M": {
                "shared_to_type": {"S": "user"},
                "shared_to_id": {"S": "user_shared"},
                "permission": {"S": "viewer"},
            }
        },
    }


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


def test_list_audit_logs_success(test_client, setup_dynamodb_tables, sample_dashboard, sample_audit_log, auth_headers):
    """監査ログ一覧取得成功（オーナー）"""
    # DashboardとAuditLogを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    audit_logs_table = dynamodb.Table(get_table_name("AuditLogs"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    # DynamoDBクライアントで直接put_item（DynamoDB形式）
    client = boto3.client("dynamodb", region_name="ap-northeast-1")
    client.put_item(
        TableName=get_table_name("AuditLogs"),
        Item=sample_audit_log,
    )
    
    # 監査ログ一覧取得
    response = test_client.get(
        "/api/audit-logs?dashboard_id=dashboard_test123",
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert len(data["data"]) > 0
    assert data["data"][0]["event_type"] == "DASHBOARD_SHARE_ADDED"


def test_list_audit_logs_forbidden(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """監査ログ一覧取得失敗（オーナー以外）"""
    # 別ユーザのDashboardを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    dashboard = sample_dashboard.copy()
    dashboard["ownerId"] = "user_other"
    table.put_item(Item=dashboard)
    
    # 監査ログ一覧取得（権限なし）
    response = test_client.get(
        "/api/audit-logs?dashboard_id=dashboard_test123",
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_list_audit_logs_with_filters(test_client, setup_dynamodb_tables, sample_dashboard, sample_audit_log, auth_headers):
    """監査ログ一覧取得（フィルタ付き）"""
    # DashboardとAuditLogを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    # DynamoDBクライアントで直接put_item（DynamoDB形式）
    client = boto3.client("dynamodb", region_name="ap-northeast-1")
    client.put_item(
        TableName=get_table_name("AuditLogs"),
        Item=sample_audit_log,
    )
    
    # イベントタイプでフィルタ
    response = test_client.get(
        "/api/audit-logs?dashboard_id=dashboard_test123&event_type=DASHBOARD_SHARE_ADDED",
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert all(log["event_type"] == "DASHBOARD_SHARE_ADDED" for log in data["data"])


def test_create_share_logs_audit(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """共有追加で監査ログが記録される"""
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
    
    # 監査ログを確認（DynamoDBクライアントで直接scan）
    client = boto3.client("dynamodb", region_name="ap-northeast-1")
    response = client.scan(TableName=get_table_name("AuditLogs"))
    items = response.get("Items", [])
    
    # 監査ログが1件記録されている
    assert len(items) > 0
    log_item = items[0]
    assert log_item["eventType"]["S"] == "DASHBOARD_SHARE_ADDED"
    assert log_item["targetId"]["S"] == "dashboard_test123"


def test_delete_share_logs_audit(test_client, setup_dynamodb_tables, sample_dashboard, sample_share, auth_headers):
    """共有削除で監査ログが記録される"""
    # DashboardとShareを作成
    dynamodb = setup_dynamodb_tables
    dashboards_table = dynamodb.Table(get_table_name("Dashboards"))
    shares_table = dynamodb.Table(get_table_name("DashboardShares"))
    
    dashboards_table.put_item(Item=sample_dashboard)
    shares_table.put_item(Item=sample_share)
    
    # 共有削除
    response = test_client.delete(
        "/api/dashboards/dashboard_test123/shares/share_test123",
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
    
    # 監査ログを確認（DynamoDBクライアントで直接scan）
    client = boto3.client("dynamodb", region_name="ap-northeast-1")
    response = client.scan(TableName=get_table_name("AuditLogs"))
    items = response.get("Items", [])
    
    # 監査ログが1件記録されている
    assert len(items) > 0
    log_item = items[0]
    assert log_item["eventType"]["S"] == "DASHBOARD_SHARE_REMOVED"
    assert log_item["targetId"]["S"] == "dashboard_test123"


def test_list_audit_logs_missing_dashboard_id(test_client, auth_headers):
    """dashboard_id未指定で400エラー"""
    response = test_client.get("/api/audit-logs", headers=auth_headers)
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "dashboard_id is required" in response.json()["error"]["message"]


def test_list_audit_logs_invalid_datetime_format(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """無効な時刻形式で400エラー"""
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    table.put_item(Item=sample_dashboard)
    
    response = test_client.get(
        "/api/audit-logs?dashboard_id=dashboard_test123&start_time=invalid",
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Invalid start_time format" in response.json()["error"]["message"]


def test_list_audit_logs_empty_result(test_client, setup_dynamodb_tables, sample_dashboard, auth_headers):
    """監査ログが存在しない場合の空リスト"""
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Dashboards"))
    table.put_item(Item=sample_dashboard)
    
    response = test_client.get(
        "/api/audit-logs?dashboard_id=dashboard_test123",
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 0
    assert data["pagination"]["total"] == 0
