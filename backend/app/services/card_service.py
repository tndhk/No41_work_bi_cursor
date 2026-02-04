"""Cardサービス"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Tuple
import uuid
import httpx

from app.db.dynamodb import get_dynamodb_client, get_table_name
from app.core.exceptions import NotFoundError, InternalError
from app.core.config import settings
from app.models.card import Card, CardCreate, CardUpdate, CardPreviewRequest, CardPreviewResponse
from app.services.dataset_service import get_dataset
from app.services.cache_service import (
    get_cached_card_preview,
    set_cached_card_preview,
    invalidate_card_preview_cache,
)


CARDS_TABLE = get_table_name("Cards")


def _item_to_card(item: dict) -> Card:
    """DynamoDBアイテムをCardモデルに変換"""
    params = {}
    if "params" in item and "M" in item["params"]:
        params = _parse_map_attribute(item["params"])
    
    used_columns = []
    if "usedColumns" in item and "L" in item["usedColumns"]:
        used_columns = [col.get("S", "") for col in item["usedColumns"]["L"]]
    
    filter_applicable = []
    if "filterApplicable" in item and "L" in item["filterApplicable"]:
        filter_applicable = [f.get("S", "") for f in item["filterApplicable"]["L"]]
    
    return Card(
        card_id=item["cardId"]["S"],
        name=item["name"]["S"],
        owner_id=item["ownerId"]["S"],
        dataset_id=item["datasetId"]["S"],
        code=item["code"]["S"],
        params=params,
        used_columns=used_columns,
        filter_applicable=filter_applicable,
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
        else:
            item[key] = {"S": str(value)}
    return item


async def create_card(user_id: str, card_data: CardCreate) -> Card:
    """Cardを作成"""
    # Datasetが存在するか確認
    dataset = await get_dataset(card_data.dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", card_data.dataset_id)
    
    card_id = f"card_{uuid.uuid4().hex[:12]}"
    now = int(datetime.utcnow().timestamp())
    
    item_data = {
        "cardId": card_id,
        "name": card_data.name,
        "ownerId": user_id,
        "datasetId": card_data.dataset_id,
        "code": card_data.code,
        "params": card_data.params or {},
        "usedColumns": card_data.used_columns or [],
        "filterApplicable": card_data.filter_applicable or [],
        "createdAt": now,
        "updatedAt": now,
    }
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=CARDS_TABLE,
        Item=_dict_to_dynamodb_item(item_data),
    )
    
    return Card(
        card_id=card_id,
        name=card_data.name,
        owner_id=user_id,
        dataset_id=card_data.dataset_id,
        code=card_data.code,
        params=card_data.params or {},
        used_columns=card_data.used_columns or [],
        filter_applicable=card_data.filter_applicable or [],
        created_at=datetime.fromtimestamp(now),
        updated_at=datetime.fromtimestamp(now),
    )


async def get_card(card_id: str) -> Optional[Card]:
    """Cardを取得"""
    client = await get_dynamodb_client()
    response = await client.get_item(
        TableName=CARDS_TABLE,
        Key={"cardId": {"S": card_id}},
    )
    
    if "Item" not in response:
        return None
    
    return _item_to_card(response["Item"])


async def list_cards(
    owner_id: Optional[str] = None,
    dataset_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    q: Optional[str] = None,
) -> Tuple[List[Card], int]:
    """Card一覧を取得"""
    client = await get_dynamodb_client()
    
    query_limit = limit + offset
    
    if dataset_id:
        response = await client.query(
            TableName=CARDS_TABLE,
            IndexName="CardsByDataset",
            KeyConditionExpression="datasetId = :datasetId",
            ExpressionAttributeValues={
                ":datasetId": {"S": dataset_id}
            },
            Limit=query_limit,
            ScanIndexForward=False,
        )
        items = response.get("Items", [])
    elif owner_id:
        response = await client.query(
            TableName=CARDS_TABLE,
            IndexName="CardsByOwner",
            KeyConditionExpression="ownerId = :ownerId",
            ExpressionAttributeValues={
                ":ownerId": {"S": owner_id}
            },
            Limit=query_limit,
            ScanIndexForward=False,
        )
        items = response.get("Items", [])
    else:
        response = await client.scan(
            TableName=CARDS_TABLE,
            Limit=query_limit,
        )
        items = response.get("Items", [])
    
    cards = [_item_to_card(item) for item in items]
    
    if dataset_id and owner_id:
        cards = [c for c in cards if c.owner_id == owner_id]
    
    if q:
        cards = [c for c in cards if q.lower() in c.name.lower()]
    
    total = len(cards)
    return cards[offset:offset+limit], total


async def update_card(card_id: str, card_data: CardUpdate) -> Card:
    """Cardを更新"""
    card = await get_card(card_id)
    if not card:
        raise NotFoundError("Card", card_id)
    
    update_expressions = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    if card_data.name is not None:
        update_expressions.append("#name = :name")
        expression_attribute_names["#name"] = "name"
        expression_attribute_values[":name"] = {"S": card_data.name}
    
    if card_data.dataset_id is not None:
        # Datasetが存在するか確認
        dataset = await get_dataset(card_data.dataset_id)
        if not dataset:
            raise NotFoundError("Dataset", card_data.dataset_id)
        
        update_expressions.append("datasetId = :datasetId")
        expression_attribute_values[":datasetId"] = {"S": card_data.dataset_id}
    
    if card_data.code is not None:
        update_expressions.append("code = :code")
        expression_attribute_values[":code"] = {"S": card_data.code}
    
    if card_data.params is not None:
        update_expressions.append("params = :params")
        expression_attribute_values[":params"] = {"M": _dict_to_dynamodb_item(card_data.params)}
    
    if card_data.used_columns is not None:
        update_expressions.append("usedColumns = :usedColumns")
        expression_attribute_values[":usedColumns"] = {"L": [{"S": col} for col in card_data.used_columns]}
    
    if card_data.filter_applicable is not None:
        update_expressions.append("filterApplicable = :filterApplicable")
        expression_attribute_values[":filterApplicable"] = {"L": [{"S": f} for f in card_data.filter_applicable]}
    
    if not update_expressions:
        return card
    
    now = int(datetime.utcnow().timestamp())
    update_expressions.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = {"N": str(now)}
    
    client = await get_dynamodb_client()
    update_expression = f"SET {', '.join(update_expressions)}"
    
    update_kwargs = {
        "TableName": CARDS_TABLE,
        "Key": {"cardId": {"S": card_id}},
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
    }
    
    if expression_attribute_names:
        update_kwargs["ExpressionAttributeNames"] = expression_attribute_names
    
    await client.update_item(**update_kwargs)
    
    # カード更新時はキャッシュを無効化
    await invalidate_card_preview_cache(card_id)
    
    return await get_card(card_id)


async def delete_card(card_id: str) -> None:
    """Cardを削除"""
    card = await get_card(card_id)
    if not card:
        raise NotFoundError("Card", card_id)
    
    # カード削除時はキャッシュを無効化
    await invalidate_card_preview_cache(card_id)
    
    client = await get_dynamodb_client()
    
    await client.delete_item(
        TableName=CARDS_TABLE,
        Key={"cardId": {"S": card_id}},
    )


async def preview_card(card_id: str, preview_request: CardPreviewRequest) -> CardPreviewResponse:
    """Cardプレビューを実行"""
    card = await get_card(card_id)
    if not card:
        raise NotFoundError("Card", card_id)
    
    # キャッシュから取得を試みる
    cached_preview = await get_cached_card_preview(
        card_id,
        preview_request.filters,
        preview_request.params,
    )
    if cached_preview is not None:
        return CardPreviewResponse(
            html=cached_preview["html"],
            used_columns=cached_preview.get("used_columns", []),
            filter_applicable=cached_preview.get("filter_applicable", []),
        )
    
    # Datasetを取得してS3パスを取得
    dataset = await get_dataset(card.dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", card.dataset_id)
    
    # Executorサービスを呼び出す
    executor_url = f"{settings.executor_endpoint}/execute/card"
    request_data = {
        "code": card.code,
        "dataset_path": dataset.s3_path,
        "filters": preview_request.filters,
        "params": preview_request.params or {},
    }
    
    try:
        async with httpx.AsyncClient(timeout=settings.executor_timeout_card + 5) as client:
            response = await client.post(executor_url, json=request_data)
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != "success":
                raise InternalError(f"Executor returned error: {result.get('detail', 'Unknown error')}")
            
            executor_result = result.get("data", {})
            preview_response = CardPreviewResponse(
                html=executor_result.get("html", ""),
                used_columns=executor_result.get("used_columns", []),
                filter_applicable=executor_result.get("filter_applicable", []),
            )
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 503:
            raise InternalError("Card execution queue is full. Please try again later.")
        elif e.response.status_code == 400:
            error_detail = e.response.json().get("detail", "Execution error")
            raise InternalError(f"Card execution failed: {error_detail}")
        else:
            raise InternalError(f"Executor service error: {e.response.status_code}")
    except httpx.TimeoutException:
        raise InternalError("Card execution timeout")
    except Exception as e:
        raise InternalError(f"Failed to execute card: {str(e)}")
    
    # キャッシュに保存
    await set_cached_card_preview(
        card_id,
        preview_request.filters,
        preview_request.params,
        preview_response.model_dump(),
        ttl_seconds=settings.cache_ttl_seconds,
    )
    
    return preview_response
