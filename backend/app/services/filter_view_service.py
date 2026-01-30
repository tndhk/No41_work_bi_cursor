"""FilterViewサービス"""
from datetime import datetime
from typing import Optional, List
import uuid

from app.db.dynamodb import get_dynamodb_client, get_table_name
from app.core.exceptions import NotFoundError
from app.models.dashboard import FilterView
from app.services.dashboard_service import get_dashboard


FILTER_VIEWS_TABLE = get_table_name("FilterViews")


def _item_to_filter_view(item: dict) -> FilterView:
    """DynamoDBアイテムをFilterViewモデルに変換"""
    filter_state = {}
    if "filterState" in item and "M" in item["filterState"]:
        filter_state = _parse_map_attribute(item["filterState"])
    
    return FilterView(
        filter_view_id=item["filterViewId"]["S"],
        dashboard_id=item["dashboardId"]["S"],
        name=item["name"]["S"],
        owner_id=item["ownerId"]["S"],
        filter_state=filter_state,
        is_shared=item.get("isShared", {}).get("BOOL", False),
        is_default=item.get("isDefault", {}).get("BOOL", False),
        created_at=datetime.fromtimestamp(int(item["createdAt"]["N"])),
        updated_at=datetime.fromtimestamp(int(item["updatedAt"]["N"])),
    )


def _parse_map_attribute(attr: dict) -> dict:
    """DynamoDBのMap属性をPython辞書に変換"""
    result = {}
    if "M" in attr:
        for key, value in attr["M"].items():
            if "S" in value:
                result[key] = value["S"]
            elif "N" in value:
                result[key] = float(value["N"]) if "." in value["N"] else int(value["N"])
            elif "BOOL" in value:
                result[key] = value["BOOL"]
            elif "M" in value:
                result[key] = _parse_map_attribute(value)
            elif "L" in value:
                result[key] = [_parse_map_attribute(v) if "M" in v else v.get("S", "") for v in value["L"]]
    return result


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
        elif isinstance(value, dict):
            item[key] = {"M": _dict_to_dynamodb_item(value)}
        elif isinstance(value, list):
            item[key] = {"L": [_dict_to_dynamodb_item(v) if isinstance(v, dict) else {"S": str(v)} for v in value]}
        else:
            item[key] = {"S": str(value)}
    return item


async def create_filter_view(
    dashboard_id: str,
    name: str,
    owner_id: str,
    filter_state: dict,
    is_shared: bool = False,
    is_default: bool = False,
) -> FilterView:
    """FilterViewを作成"""
    # Dashboardが存在するか確認
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    filter_view_id = f"filterview_{uuid.uuid4().hex[:12]}"
    now = int(datetime.utcnow().timestamp())
    
    item_data = {
        "filterViewId": filter_view_id,
        "dashboardId": dashboard_id,
        "name": name,
        "ownerId": owner_id,
        "filterState": filter_state,
        "isShared": is_shared,
        "isDefault": is_default,
        "createdAt": now,
        "updatedAt": now,
    }
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=FILTER_VIEWS_TABLE,
        Item=_dict_to_dynamodb_item(item_data),
    )
    
    return FilterView(
        filter_view_id=filter_view_id,
        dashboard_id=dashboard_id,
        name=name,
        owner_id=owner_id,
        filter_state=filter_state,
        is_shared=is_shared,
        is_default=is_default,
        created_at=datetime.fromtimestamp(now),
        updated_at=datetime.fromtimestamp(now),
    )


async def get_filter_view(filter_view_id: str) -> Optional[FilterView]:
    """FilterViewを取得"""
    client = await get_dynamodb_client()
    response = await client.get_item(
        TableName=FILTER_VIEWS_TABLE,
        Key={"filterViewId": {"S": filter_view_id}},
    )
    
    if "Item" not in response:
        return None
    
    return _item_to_filter_view(response["Item"])


async def list_filter_views(dashboard_id: str) -> List[FilterView]:
    """DashboardのFilterView一覧を取得"""
    client = await get_dynamodb_client()
    
    response = await client.query(
        TableName=FILTER_VIEWS_TABLE,
        IndexName="FilterViewsByDashboard",
        KeyConditionExpression="dashboardId = :dashboardId",
        ExpressionAttributeValues={
            ":dashboardId": {"S": dashboard_id}
        },
    )
    
    return [_item_to_filter_view(item) for item in response.get("Items", [])]


async def update_filter_view(
    filter_view_id: str,
    name: Optional[str] = None,
    filter_state: Optional[dict] = None,
    is_shared: Optional[bool] = None,
    is_default: Optional[bool] = None,
) -> FilterView:
    """FilterViewを更新"""
    filter_view = await get_filter_view(filter_view_id)
    if not filter_view:
        raise NotFoundError("FilterView", filter_view_id)
    
    update_expressions = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    if name is not None:
        update_expressions.append("#name = :name")
        expression_attribute_names["#name"] = "name"
        expression_attribute_values[":name"] = {"S": name}
    
    if filter_state is not None:
        update_expressions.append("filterState = :filterState")
        expression_attribute_values[":filterState"] = {"M": _dict_to_dynamodb_item(filter_state)}
    
    if is_shared is not None:
        update_expressions.append("isShared = :isShared")
        expression_attribute_values[":isShared"] = {"BOOL": is_shared}
    
    if is_default is not None:
        update_expressions.append("isDefault = :isDefault")
        expression_attribute_values[":isDefault"] = {"BOOL": is_default}
    
    if not update_expressions:
        return filter_view
    
    now = int(datetime.utcnow().timestamp())
    update_expressions.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = {"N": str(now)}
    
    client = await get_dynamodb_client()
    update_expression = f"SET {', '.join(update_expressions)}"
    
    update_kwargs = {
        "TableName": FILTER_VIEWS_TABLE,
        "Key": {"filterViewId": {"S": filter_view_id}},
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
    }
    
    if expression_attribute_names:
        update_kwargs["ExpressionAttributeNames"] = expression_attribute_names
    
    await client.update_item(**update_kwargs)
    
    return await get_filter_view(filter_view_id)


async def delete_filter_view(filter_view_id: str) -> None:
    """FilterViewを削除"""
    filter_view = await get_filter_view(filter_view_id)
    if not filter_view:
        raise NotFoundError("FilterView", filter_view_id)
    
    client = await get_dynamodb_client()
    
    await client.delete_item(
        TableName=FILTER_VIEWS_TABLE,
        Key={"filterViewId": {"S": filter_view_id}},
    )
