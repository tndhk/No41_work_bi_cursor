"""Dashboardサービス"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import uuid

from app.db.dynamodb import get_dynamodb_client, get_table_name
from app.core.exceptions import NotFoundError
from app.models.dashboard import Dashboard, DashboardCreate, DashboardUpdate
from app.services.card_service import get_card


DASHBOARDS_TABLE = get_table_name("Dashboards")


def _item_to_dashboard(item: dict) -> Dashboard:
    """DynamoDBアイテムをDashboardモデルに変換"""
    layout = {}
    if "layout" in item and "M" in item["layout"]:
        layout = _parse_map_attribute(item["layout"])
    
    filters = []
    if "filters" in item and "L" in item["filters"]:
        filters = [_parse_map_attribute(f.get("M", {})) for f in item["filters"]["L"]]
    
    return Dashboard(
        dashboard_id=item["dashboardId"]["S"],
        name=item["name"]["S"],
        owner_id=item["ownerId"]["S"],
        layout=layout,
        filters=filters,
        default_filter_view_id=item.get("defaultFilterViewId", {}).get("S") if "defaultFilterViewId" in item else None,
        created_at=datetime.fromtimestamp(int(item["createdAt"]["N"])),
        updated_at=datetime.fromtimestamp(int(item["updatedAt"]["N"])),
    )


def _parse_map_attribute(attr: dict) -> Dict[str, Any]:
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
        elif value is None:
            continue  # None値はスキップ
        else:
            item[key] = {"S": str(value)}
    return item


async def create_dashboard(user_id: str, dashboard_data: DashboardCreate) -> Dashboard:
    """Dashboardを作成"""
    dashboard_id = f"dashboard_{uuid.uuid4().hex[:12]}"
    now = int(datetime.utcnow().timestamp())
    
    item_data = {
        "dashboardId": dashboard_id,
        "name": dashboard_data.name,
        "ownerId": user_id,
        "layout": dashboard_data.layout or {},
        "filters": dashboard_data.filters or [],
        "createdAt": now,
        "updatedAt": now,
    }
    
    if dashboard_data.default_filter_view_id:
        item_data["defaultFilterViewId"] = dashboard_data.default_filter_view_id
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=DASHBOARDS_TABLE,
        Item=_dict_to_dynamodb_item(item_data),
    )
    
    return Dashboard(
        dashboard_id=dashboard_id,
        name=dashboard_data.name,
        owner_id=user_id,
        layout=dashboard_data.layout or {},
        filters=dashboard_data.filters or [],
        default_filter_view_id=dashboard_data.default_filter_view_id,
        created_at=datetime.fromtimestamp(now),
        updated_at=datetime.fromtimestamp(now),
    )


async def get_dashboard(dashboard_id: str) -> Optional[Dashboard]:
    """Dashboardを取得"""
    client = await get_dynamodb_client()
    response = await client.get_item(
        TableName=DASHBOARDS_TABLE,
        Key={"dashboardId": {"S": dashboard_id}},
    )
    
    if "Item" not in response:
        return None
    
    return _item_to_dashboard(response["Item"])


async def list_dashboards(
    owner_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    q: Optional[str] = None,
) -> Tuple[List[Dashboard], int]:
    """Dashboard一覧を取得"""
    client = await get_dynamodb_client()
    
    if owner_id:
        # GSIを使用してownerIdでクエリ
        response = await client.query(
            TableName=DASHBOARDS_TABLE,
            IndexName="DashboardsByOwner",
            KeyConditionExpression="ownerId = :ownerId",
            ExpressionAttributeValues={
                ":ownerId": {"S": owner_id}
            },
            Limit=limit + offset,
            ScanIndexForward=False,  # 新しい順
        )
        items = response.get("Items", [])
    else:
        # Scan
        response = await client.scan(
            TableName=DASHBOARDS_TABLE,
            Limit=limit + offset,
        )
        items = response.get("Items", [])
    
    dashboards = [_item_to_dashboard(item) for item in items]
    
    if q:
        dashboards = [d for d in dashboards if q.lower() in d.name.lower()]
    
    total = len(dashboards)
    return dashboards[offset:offset+limit], total


async def update_dashboard(dashboard_id: str, dashboard_data: DashboardUpdate) -> Dashboard:
    """Dashboardを更新"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    update_expressions = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    if dashboard_data.name is not None:
        update_expressions.append("#name = :name")
        expression_attribute_names["#name"] = "name"
        expression_attribute_values[":name"] = {"S": dashboard_data.name}
    
    if dashboard_data.layout is not None:
        update_expressions.append("layout = :layout")
        expression_attribute_values[":layout"] = {"M": _dict_to_dynamodb_item(dashboard_data.layout)}
    
    if dashboard_data.filters is not None:
        update_expressions.append("filters = :filters")
        expression_attribute_values[":filters"] = {"L": [{"M": _dict_to_dynamodb_item(f)} for f in dashboard_data.filters]}
    
    if dashboard_data.default_filter_view_id is not None:
        update_expressions.append("defaultFilterViewId = :defaultFilterViewId")
        expression_attribute_values[":defaultFilterViewId"] = {"S": dashboard_data.default_filter_view_id}
    
    if not update_expressions:
        return dashboard
    
    now = int(datetime.utcnow().timestamp())
    update_expressions.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = {"N": str(now)}
    
    client = await get_dynamodb_client()
    update_expression = f"SET {', '.join(update_expressions)}"
    
    update_kwargs = {
        "TableName": DASHBOARDS_TABLE,
        "Key": {"dashboardId": {"S": dashboard_id}},
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
    }
    
    if expression_attribute_names:
        update_kwargs["ExpressionAttributeNames"] = expression_attribute_names
    
    await client.update_item(**update_kwargs)
    
    return await get_dashboard(dashboard_id)


async def delete_dashboard(dashboard_id: str) -> None:
    """Dashboardを削除"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    client = await get_dynamodb_client()
    
    await client.delete_item(
        TableName=DASHBOARDS_TABLE,
        Key={"dashboardId": {"S": dashboard_id}},
    )


async def clone_dashboard(dashboard_id: str, user_id: str, new_name: Optional[str] = None) -> Dashboard:
    """Dashboardを複製"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    new_name = new_name or f"{dashboard.name} (Copy)"
    
    dashboard_data = DashboardCreate(
        name=new_name,
        layout=dashboard.layout,
        filters=dashboard.filters,
        default_filter_view_id=dashboard.default_filter_view_id,
    )
    
    return await create_dashboard(user_id, dashboard_data)


async def get_referenced_datasets(dashboard_id: str) -> List[str]:
    """Dashboardが参照しているDataset一覧を取得"""
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    # layoutからcard_idを取得
    card_ids = []
    if "cards" in dashboard.layout:
        cards = dashboard.layout["cards"]
        if isinstance(cards, list):
            for card in cards:
                if isinstance(card, dict) and "cardId" in card:
                    card_ids.append(card["cardId"])
        elif isinstance(cards, dict):
            for card_id in cards.keys():
                card_ids.append(card_id)
    
    # 各Cardからdataset_idを取得
    dataset_ids = set()
    for card_id in card_ids:
        card = await get_card(card_id)
        if card:
            dataset_ids.add(card.dataset_id)
    
    return list(dataset_ids)
