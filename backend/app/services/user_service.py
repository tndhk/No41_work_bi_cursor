"""Userサービス"""
from datetime import datetime
from typing import Optional
import uuid

from app.db.dynamodb import get_dynamodb_client, get_table_name
from app.core.security import hash_password
from app.core.exceptions import NotFoundError
from app.models.user import User, UserCreate, UserUpdate, UserInDB


TABLE_NAME = get_table_name("Users")


def _item_to_user(item: dict) -> User:
    """DynamoDBアイテムをUserモデルに変換"""
    return User(
        user_id=item["userId"]["S"],
        email=item["email"]["S"],
        name=item["name"]["S"],
        created_at=datetime.fromtimestamp(int(item["createdAt"]["N"])),
        updated_at=datetime.fromtimestamp(int(item["updatedAt"]["N"])),
    )


def _item_to_user_in_db(item: dict) -> UserInDB:
    """DynamoDBアイテムをUserInDBモデルに変換"""
    return UserInDB(
        user_id=item["userId"]["S"],
        email=item["email"]["S"],
        name=item["name"]["S"],
        password_hash=item["passwordHash"]["S"],
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
        else:
            item[key] = {"S": str(value)}
    return item


async def create_user(user_data: UserCreate) -> User:
    """ユーザを作成"""
    user_id = f"user_{uuid.uuid4().hex[:12]}"
    now = int(datetime.utcnow().timestamp())
    
    item_data = {
        "userId": user_id,
        "email": user_data.email,
        "name": user_data.name,
        "passwordHash": hash_password(user_data.password),
        "createdAt": now,
        "updatedAt": now,
    }
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=TABLE_NAME,
        Item=_dict_to_dynamodb_item(item_data),
    )
    
    return User(
        user_id=user_id,
        email=user_data.email,
        name=user_data.name,
        created_at=datetime.fromtimestamp(now),
        updated_at=datetime.fromtimestamp(now),
    )


async def get_user(user_id: str) -> Optional[User]:
    """ユーザを取得"""
    client = await get_dynamodb_client()
    response = await client.get_item(
        TableName=TABLE_NAME,
        Key={"userId": {"S": user_id}},
    )
    
    if "Item" not in response:
        return None
    
    return _item_to_user(response["Item"])


async def get_user_by_email(email: str) -> Optional[UserInDB]:
    """メールアドレスでユーザを取得"""
    client = await get_dynamodb_client()
    
    # Scan + FilterExpressionで検索（MVP段階では許容）
    # 本番環境ではGSIを作成してクエリすることを推奨
    response = await client.scan(
        TableName=TABLE_NAME,
        FilterExpression="email = :email",
        ExpressionAttributeValues={
            ":email": {"S": email}
        },
        Limit=1,
    )
    
    items = response.get("Items", [])
    if not items:
        return None
    
    return _item_to_user_in_db(items[0])


async def list_users(limit: int = 20, offset: int = 0, q: Optional[str] = None) -> tuple[list[User], int]:
    """ユーザ一覧を取得"""
    client = await get_dynamodb_client()
    
    # スキャン（本番ではGSI + クエリを使用）
    response = await client.scan(
        TableName=TABLE_NAME,
        Limit=limit,
    )
    
    users = [_item_to_user(item) for item in response.get("Items", [])]
    
    # 簡易的な検索（本番ではFilterExpressionを使用）
    if q:
        users = [u for u in users if q.lower() in u.name.lower() or q.lower() in u.email.lower()]
    
    total = len(users)
    return users[offset:offset+limit], total


async def update_user(user_id: str, user_data: UserUpdate) -> User:
    """ユーザを更新"""
    user = await get_user(user_id)
    if not user:
        raise NotFoundError("User", user_id)
    
    update_expressions = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    if user_data.name is not None:
        update_expressions.append("#name = :name")
        expression_attribute_names["#name"] = "name"
        expression_attribute_values[":name"] = {"S": user_data.name}
    
    if user_data.email is not None:
        update_expressions.append("email = :email")
        expression_attribute_values[":email"] = {"S": user_data.email}
    
    if not update_expressions:
        return user
    
    now = int(datetime.utcnow().timestamp())
    update_expressions.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = {"N": str(now)}
    
    client = await get_dynamodb_client()
    update_expression = f"SET {', '.join(update_expressions)}"
    
    update_kwargs = {
        "TableName": TABLE_NAME,
        "Key": {"userId": {"S": user_id}},
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
    }
    
    if expression_attribute_names:
        update_kwargs["ExpressionAttributeNames"] = expression_attribute_names
    
    await client.update_item(**update_kwargs)
    
    return await get_user(user_id)
