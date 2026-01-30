"""Groups APIのテスト"""
import pytest
from fastapi import status
import boto3

from app.db.dynamodb import get_table_name




def test_list_groups_success(test_client, setup_dynamodb_tables, sample_group, auth_headers):
    """グループ一覧取得成功"""
    # グループを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Groups"))
    table.put_item(Item=sample_group)
    
    # 一覧取得
    response = test_client.get("/api/groups", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert "pagination" in data




def test_create_group_success(test_client, setup_dynamodb_tables, auth_headers):
    """グループ作成成功"""
    response = test_client.post(
        "/api/groups",
        json={"name": "New Group"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert data["data"]["name"] == "New Group"




def test_get_group_success(test_client, setup_dynamodb_tables, sample_group, auth_headers):
    """グループ詳細取得成功"""
    # グループを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Groups"))
    table.put_item(Item=sample_group)
    
    # 詳細取得
    response = test_client.get("/api/groups/group_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "data" in data
    assert data["data"]["group_id"] == "group_test123"




def test_get_group_not_found(test_client, setup_dynamodb_tables, auth_headers):
    """グループ詳細取得失敗（NotFound）"""
    response = test_client.get("/api/groups/group_nonexistent", headers=auth_headers)
    
    assert response.status_code == status.HTTP_404_NOT_FOUND
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "NOT_FOUND"




def test_update_group_success(test_client, setup_dynamodb_tables, sample_group, auth_headers):
    """グループ更新成功"""
    # グループを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Groups"))
    table.put_item(Item=sample_group)
    
    # 更新
    response = test_client.put(
        "/api/groups/group_test123",
        json={"name": "Updated Group"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["data"]["name"] == "Updated Group"




def test_update_group_not_found(test_client, setup_dynamodb_tables, auth_headers):
    """グループ更新失敗（NotFound）"""
    response = test_client.put(
        "/api/groups/group_nonexistent",
        json={"name": "Updated Group"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_404_NOT_FOUND




def test_delete_group_success(test_client, setup_dynamodb_tables, sample_group, auth_headers):
    """グループ削除成功"""
    # グループを作成
    dynamodb = setup_dynamodb_tables
    table = dynamodb.Table(get_table_name("Groups"))
    table.put_item(Item=sample_group)
    
    # 削除
    response = test_client.delete("/api/groups/group_test123", headers=auth_headers)
    
    assert response.status_code == status.HTTP_204_NO_CONTENT




def test_add_group_member_success(test_client, setup_dynamodb_tables, sample_group, sample_user, auth_headers):
    """グループメンバー追加成功"""
    # グループとユーザを作成
    dynamodb = setup_dynamodb_tables
    groups_table = dynamodb.Table(get_table_name("Groups"))
    users_table = dynamodb.Table(get_table_name("Users"))
    groups_table.put_item(Item=sample_group)
    users_table.put_item(Item=sample_user)
    
    # メンバー追加
    response = test_client.post(
        "/api/groups/group_test123/members",
        json={"user_id": "user_test123"},
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert "data" in data
    assert data["data"]["user_id"] == "user_test123"




def test_remove_group_member_success(test_client, setup_dynamodb_tables, sample_group, sample_user, auth_headers):
    """グループメンバー削除成功"""
    # グループとユーザを作成
    dynamodb = setup_dynamodb_tables
    groups_table = dynamodb.Table(get_table_name("Groups"))
    users_table = dynamodb.Table(get_table_name("Users"))
    members_table = dynamodb.Table(get_table_name("GroupMembers"))
    
    groups_table.put_item(Item=sample_group)
    users_table.put_item(Item=sample_user)
    
    # メンバーを追加
    from datetime import datetime
    members_table.put_item(Item={
        "groupId": "group_test123",
        "userId": "user_test123",
        "addedAt": int(datetime.utcnow().timestamp()),
    })
    
    # メンバー削除
    response = test_client.delete(
        "/api/groups/group_test123/members/user_test123",
        headers=auth_headers,
    )
    
    assert response.status_code == status.HTTP_204_NO_CONTENT
