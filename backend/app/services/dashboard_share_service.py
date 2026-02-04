"""Dashboard Shareサービス"""
from datetime import datetime
from typing import Optional, List
import uuid

from app.db.dynamodb import get_dynamodb_client, get_table_name
from app.core.exceptions import NotFoundError
from app.models.dashboard import DashboardShare
from app.services.dashboard_service import get_dashboard
from app.services.group_service import get_group_member
from app.services.dashboard_service import get_dashboard


DASHBOARD_SHARES_TABLE = get_table_name("DashboardShares")


def _item_to_share(item: dict) -> DashboardShare:
    """DynamoDBアイテムをDashboardShareモデルに変換"""
    return DashboardShare(
        share_id=item["shareId"]["S"],
        dashboard_id=item["dashboardId"]["S"],
        shared_to_type=item["sharedToType"]["S"],
        shared_to_id=item["sharedToId"]["S"],
        permission=item["permission"]["S"],
        shared_by=item["sharedBy"]["S"],
        created_at=datetime.fromtimestamp(int(item["createdAt"]["N"])),
    )


def _dict_to_dynamodb_item(data: dict) -> dict:
    """辞書をDynamoDBアイテム形式に変換"""
    item = {}
    for key, value in data.items():
        if isinstance(value, str):
            item[key] = {"S": value}
        elif isinstance(value, (int, float)):
            item[key] = {"N": str(value)}
        elif isinstance(value, bool):
            item[key] = {"BOOL": value}
        else:
            item[key] = {"S": str(value)}
    return item


async def create_share(
    dashboard_id: str,
    shared_to_type: str,
    shared_to_id: str,
    permission: str,
    shared_by: str,
) -> DashboardShare:
    """共有を作成"""
    # Dashboardが存在するか確認
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    share_id = f"share_{uuid.uuid4().hex[:12]}"
    now = int(datetime.utcnow().timestamp())
    
    item_data = {
        "shareId": share_id,
        "dashboardId": dashboard_id,
        "sharedToType": shared_to_type,
        "sharedToId": shared_to_id,
        "permission": permission,
        "sharedBy": shared_by,
        "createdAt": now,
    }
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=DASHBOARD_SHARES_TABLE,
        Item=_dict_to_dynamodb_item(item_data),
    )
    
    return DashboardShare(
        share_id=share_id,
        dashboard_id=dashboard_id,
        shared_to_type=shared_to_type,
        shared_to_id=shared_to_id,
        permission=permission,
        shared_by=shared_by,
        created_at=datetime.fromtimestamp(now),
    )


async def get_share(share_id: str) -> Optional[DashboardShare]:
    """共有を取得"""
    client = await get_dynamodb_client()
    response = await client.get_item(
        TableName=DASHBOARD_SHARES_TABLE,
        Key={"shareId": {"S": share_id}},
    )
    
    if "Item" not in response:
        return None
    
    return _item_to_share(response["Item"])


async def list_shares(dashboard_id: str) -> List[DashboardShare]:
    """Dashboardの共有一覧を取得"""
    client = await get_dynamodb_client()
    
    response = await client.query(
        TableName=DASHBOARD_SHARES_TABLE,
        IndexName="SharesByDashboard",
        KeyConditionExpression="dashboardId = :dashboardId",
        ExpressionAttributeValues={
            ":dashboardId": {"S": dashboard_id}
        },
    )
    
    return [_item_to_share(item) for item in response.get("Items", [])]


async def update_share(share_id: str, permission: str) -> DashboardShare:
    """共有を更新"""
    share = await get_share(share_id)
    if not share:
        raise NotFoundError("Share", share_id)
    
    client = await get_dynamodb_client()
    await client.update_item(
        TableName=DASHBOARD_SHARES_TABLE,
        Key={"shareId": {"S": share_id}},
        UpdateExpression="SET #permission = :permission",
        ExpressionAttributeNames={
            "#permission": "permission"
        },
        ExpressionAttributeValues={
            ":permission": {"S": permission}
        },
    )
    
    updated_share = await get_share(share_id)
    return updated_share


async def delete_share(share_id: str) -> None:
    """共有を削除"""
    share = await get_share(share_id)
    if not share:
        raise NotFoundError("Share", share_id)
    
    client = await get_dynamodb_client()
    
    await client.delete_item(
        TableName=DASHBOARD_SHARES_TABLE,
        Key={"shareId": {"S": share_id}},
    )


async def check_dashboard_permission(dashboard_id: str, user_id: str) -> Optional[str]:
    """ユーザのDashboard権限を取得"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        return None
    
    # Ownerチェック
    if dashboard.owner_id == user_id:
        return "owner"
    
    # Shareをチェック
    shares = await list_shares(dashboard_id)
    for share in shares:
        if share.shared_to_type == "user" and share.shared_to_id == user_id:
            return share.permission
        elif share.shared_to_type == "group":
            # Groupメンバーシップチェック
            group_member = await get_group_member(share.shared_to_id, user_id)
            if group_member is not None:
                return share.permission
    
    return None
