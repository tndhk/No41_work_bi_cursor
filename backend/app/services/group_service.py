"""Groupサービス"""
from datetime import datetime
from typing import Optional, List
import uuid

from app.db.dynamodb import get_dynamodb_client, get_table_name
from app.core.exceptions import NotFoundError
from app.models.group import Group, GroupCreate, GroupUpdate, GroupMember


GROUPS_TABLE = get_table_name("Groups")
GROUP_MEMBERS_TABLE = get_table_name("GroupMembers")


def _item_to_group(item: dict) -> Group:
    """DynamoDBアイテムをGroupモデルに変換"""
    return Group(
        group_id=item["groupId"]["S"],
        name=item["name"]["S"],
        created_at=datetime.fromtimestamp(int(item["createdAt"]["N"])),
        updated_at=datetime.fromtimestamp(int(item["updatedAt"]["N"])),
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


async def create_group(group_data: GroupCreate) -> Group:
    """グループを作成"""
    group_id = f"group_{uuid.uuid4().hex[:12]}"
    now = int(datetime.utcnow().timestamp())
    
    item_data = {
        "groupId": group_id,
        "name": group_data.name,
        "createdAt": now,
        "updatedAt": now,
    }
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=GROUPS_TABLE,
        Item=_dict_to_dynamodb_item(item_data),
    )
    
    return Group(
        group_id=group_id,
        name=group_data.name,
        created_at=datetime.fromtimestamp(now),
        updated_at=datetime.fromtimestamp(now),
    )


async def get_group(group_id: str) -> Optional[Group]:
    """グループを取得"""
    client = await get_dynamodb_client()
    response = await client.get_item(
        TableName=GROUPS_TABLE,
        Key={"groupId": {"S": group_id}},
    )
    
    if "Item" not in response:
        return None
    
    return _item_to_group(response["Item"])


async def list_groups(limit: int = 20, offset: int = 0, q: Optional[str] = None) -> tuple[List[Group], int]:
    """グループ一覧を取得"""
    client = await get_dynamodb_client()
    
    response = await client.scan(
        TableName=GROUPS_TABLE,
        Limit=limit + offset,
    )
    
    groups = [_item_to_group(item) for item in response.get("Items", [])]
    
    if q:
        groups = [g for g in groups if q.lower() in g.name.lower()]
    
    total = len(groups)
    return groups[offset:offset+limit], total


async def update_group(group_id: str, group_data: GroupUpdate) -> Group:
    """グループを更新"""
    group = await get_group(group_id)
    if not group:
        raise NotFoundError("Group", group_id)
    
    update_expressions = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    if group_data.name is not None:
        update_expressions.append("#name = :name")
        expression_attribute_names["#name"] = "name"
        expression_attribute_values[":name"] = {"S": group_data.name}
    
    if not update_expressions:
        return group
    
    now = int(datetime.utcnow().timestamp())
    update_expressions.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = {"N": str(now)}
    
    client = await get_dynamodb_client()
    update_expression = f"SET {', '.join(update_expressions)}"
    
    update_kwargs = {
        "TableName": GROUPS_TABLE,
        "Key": {"groupId": {"S": group_id}},
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
    }
    
    if expression_attribute_names:
        update_kwargs["ExpressionAttributeNames"] = expression_attribute_names
    
    await client.update_item(**update_kwargs)
    
    return await get_group(group_id)


async def delete_group(group_id: str) -> None:
    """グループを削除"""
    group = await get_group(group_id)
    if not group:
        raise NotFoundError("Group", group_id)
    
    client = await get_dynamodb_client()
    
    # グループを削除
    await client.delete_item(
        TableName=GROUPS_TABLE,
        Key={"groupId": {"S": group_id}},
    )
    
    # メンバーシップも削除（GroupMembersテーブルから）
    # まずメンバー一覧を取得
    members = await list_group_members(group_id)
    for member in members:
        await remove_group_member(group_id, member["userId"])


async def add_group_member(group_id: str, user_id: str) -> GroupMember:
    """グループにメンバーを追加"""
    # グループが存在するか確認
    group = await get_group(group_id)
    if not group:
        raise NotFoundError("Group", group_id)
    
    # 既にメンバーか確認
    existing = await get_group_member(group_id, user_id)
    if existing:
        return existing
    
    now = int(datetime.utcnow().timestamp())
    
    item_data = {
        "groupId": group_id,
        "userId": user_id,
        "addedAt": now,
    }
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=GROUP_MEMBERS_TABLE,
        Item=_dict_to_dynamodb_item(item_data),
    )
    
    return GroupMember(
        group_id=group_id,
        user_id=user_id,
        added_at=datetime.fromtimestamp(now),
    )


async def remove_group_member(group_id: str, user_id: str) -> None:
    """グループからメンバーを削除"""
    client = await get_dynamodb_client()
    
    await client.delete_item(
        TableName=GROUP_MEMBERS_TABLE,
        Key={
            "groupId": {"S": group_id},
            "userId": {"S": user_id},
        },
    )


async def get_group_member(group_id: str, user_id: str) -> Optional[GroupMember]:
    """グループメンバーを取得"""
    client = await get_dynamodb_client()
    response = await client.get_item(
        TableName=GROUP_MEMBERS_TABLE,
        Key={
            "groupId": {"S": group_id},
            "userId": {"S": user_id},
        },
    )
    
    if "Item" not in response:
        return None
    
    item = response["Item"]
    return GroupMember(
        group_id=item["groupId"]["S"],
        user_id=item["userId"]["S"],
        added_at=datetime.fromtimestamp(int(item["addedAt"]["N"])),
    )


async def list_group_members(group_id: str) -> List[dict]:
    """グループのメンバー一覧を取得"""
    client = await get_dynamodb_client()
    
    response = await client.query(
        TableName=GROUP_MEMBERS_TABLE,
        KeyConditionExpression="groupId = :groupId",
        ExpressionAttributeValues={
            ":groupId": {"S": group_id}
        },
    )
    
    members = []
    for item in response.get("Items", []):
        members.append({
            "userId": item["userId"]["S"],
            "addedAt": datetime.fromtimestamp(int(item["addedAt"]["N"])).isoformat(),
        })
    
    return members
