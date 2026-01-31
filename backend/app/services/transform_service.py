"""Transformサービス - TDD実装中"""
from datetime import datetime
from typing import Optional, List, Tuple
import uuid

from app.db.dynamodb import get_dynamodb_client, get_table_name
from app.core.exceptions import NotFoundError
from app.models.transform import Transform, TransformCreate, TransformUpdate, TransformExecution
from app.services.dataset_service import get_dataset


TRANSFORMS_TABLE = get_table_name("Transforms")
EXECUTIONS_TABLE = get_table_name("TransformExecutions")


def _item_to_transform(item: dict) -> Transform:
    """DynamoDBアイテムをTransformモデルに変換"""
    params = {}
    if "params" in item and "M" in item["params"]:
        params = _parse_map_attribute(item["params"])
    
    input_dataset_ids = []
    if "inputDatasetIds" in item and "L" in item["inputDatasetIds"]:
        input_dataset_ids = [ds_id.get("S", "") for ds_id in item["inputDatasetIds"]["L"]]
    
    output_dataset_id = None
    if "outputDatasetId" in item and "S" in item["outputDatasetId"]:
        output_dataset_id = item["outputDatasetId"]["S"]
    
    schedule = None
    if "schedule" in item and "S" in item["schedule"]:
        schedule = item["schedule"]["S"]
    
    last_executed_at = None
    if "lastExecutedAt" in item and "N" in item["lastExecutedAt"]:
        last_executed_at = datetime.fromtimestamp(int(item["lastExecutedAt"]["N"]))
    
    return Transform(
        transform_id=item["transformId"]["S"],
        name=item["name"]["S"],
        owner_id=item["ownerId"]["S"],
        code=item["code"]["S"],
        input_dataset_ids=input_dataset_ids,
        output_dataset_id=output_dataset_id,
        params=params,
        schedule=schedule,
        created_at=datetime.fromtimestamp(int(item["createdAt"]["N"])),
        updated_at=datetime.fromtimestamp(int(item["updatedAt"]["N"])),
        last_executed_at=last_executed_at,
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
        elif value is None:
            continue
        else:
            item[key] = {"S": str(value)}
    return item


async def create_transform(user_id: str, transform_data: TransformCreate) -> Transform:
    """Transformを作成"""
    # 入力Datasetが存在するか確認
    for dataset_id in transform_data.input_dataset_ids:
        dataset = await get_dataset(dataset_id)
        if not dataset:
            raise NotFoundError("Dataset", dataset_id)
    
    transform_id = f"transform_{uuid.uuid4().hex[:12]}"
    now = int(datetime.utcnow().timestamp())
    
    item_data = {
        "transformId": transform_id,
        "name": transform_data.name,
        "ownerId": user_id,
        "code": transform_data.code,
        "inputDatasetIds": transform_data.input_dataset_ids,
        "params": transform_data.params or {},
        "createdAt": now,
        "updatedAt": now,
    }
    
    if transform_data.schedule:
        item_data["schedule"] = transform_data.schedule
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=TRANSFORMS_TABLE,
        Item=_dict_to_dynamodb_item(item_data),
    )
    
    return Transform(
        transform_id=transform_id,
        name=transform_data.name,
        owner_id=user_id,
        code=transform_data.code,
        input_dataset_ids=transform_data.input_dataset_ids,
        output_dataset_id=None,
        params=transform_data.params or {},
        schedule=transform_data.schedule,
        created_at=datetime.fromtimestamp(now),
        updated_at=datetime.fromtimestamp(now),
        last_executed_at=None,
    )


async def list_transforms(
    owner_id: Optional[str] = None,
    limit: int = 20,
    offset: int = 0,
    q: Optional[str] = None,
) -> Tuple[List[Transform], int]:
    """Transform一覧を取得"""
    client = await get_dynamodb_client()
    
    if owner_id:
        # GSIを使用してownerIdでクエリ
        response = await client.query(
            TableName=TRANSFORMS_TABLE,
            IndexName="TransformsByOwner",
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
            TableName=TRANSFORMS_TABLE,
            Limit=limit + offset,
        )
        items = response.get("Items", [])
    
    transforms = [_item_to_transform(item) for item in items]
    
    if q:
        transforms = [t for t in transforms if q.lower() in t.name.lower()]
    
    total = len(transforms)
    return transforms[offset:offset+limit], total


async def get_transform(transform_id: str) -> Optional[Transform]:
    """Transformを取得"""
    client = await get_dynamodb_client()
    response = await client.get_item(
        TableName=TRANSFORMS_TABLE,
        Key={"transformId": {"S": transform_id}},
    )
    
    if "Item" not in response:
        return None
    
    return _item_to_transform(response["Item"])


async def update_transform(transform_id: str, transform_data: TransformUpdate) -> Transform:
    """Transformを更新"""
    transform = await get_transform(transform_id)
    if not transform:
        raise NotFoundError("Transform", transform_id)
    
    update_expressions = []
    expression_attribute_values = {}
    expression_attribute_names = {}
    
    if transform_data.name is not None:
        update_expressions.append("#name = :name")
        expression_attribute_names["#name"] = "name"
        expression_attribute_values[":name"] = {"S": transform_data.name}
    
    if transform_data.code is not None:
        update_expressions.append("code = :code")
        expression_attribute_values[":code"] = {"S": transform_data.code}
    
    if transform_data.input_dataset_ids is not None:
        # 入力Datasetが存在するか確認
        for dataset_id in transform_data.input_dataset_ids:
            dataset = await get_dataset(dataset_id)
            if not dataset:
                raise NotFoundError("Dataset", dataset_id)
        
        update_expressions.append("inputDatasetIds = :inputDatasetIds")
        expression_attribute_values[":inputDatasetIds"] = {"L": [{"S": ds_id} for ds_id in transform_data.input_dataset_ids]}
    
    if transform_data.params is not None:
        update_expressions.append("params = :params")
        expression_attribute_values[":params"] = {"M": _dict_to_dynamodb_item(transform_data.params)}
    
    if transform_data.schedule is not None:
        if transform_data.schedule == "":
            # 空文字列の場合はスケジュールを削除
            update_expressions.append("REMOVE schedule")
        else:
            update_expressions.append("schedule = :schedule")
            expression_attribute_values[":schedule"] = {"S": transform_data.schedule}
    
    if not update_expressions:
        return transform
    
    now = int(datetime.utcnow().timestamp())
    update_expressions.append("updatedAt = :updatedAt")
    expression_attribute_values[":updatedAt"] = {"N": str(now)}
    
    client = await get_dynamodb_client()
    
    # SET句とREMOVE句を分離
    set_expressions = [e for e in update_expressions if not e.startswith('REMOVE')]
    remove_expressions = [e.replace('REMOVE ', '') for e in update_expressions if e.startswith('REMOVE')]
    
    update_parts = []
    if set_expressions:
        update_parts.append(f"SET {', '.join(set_expressions)}")
    if remove_expressions:
        update_parts.append(f"REMOVE {', '.join(remove_expressions)}")
    
    update_expression = " ".join(update_parts)
    
    update_kwargs = {
        "TableName": TRANSFORMS_TABLE,
        "Key": {"transformId": {"S": transform_id}},
        "UpdateExpression": update_expression,
        "ExpressionAttributeValues": expression_attribute_values,
    }
    
    if expression_attribute_names:
        update_kwargs["ExpressionAttributeNames"] = expression_attribute_names
    
    await client.update_item(**update_kwargs)
    
    return await get_transform(transform_id)


async def delete_transform(transform_id: str) -> None:
    """Transformを削除"""
    transform = await get_transform(transform_id)
    if not transform:
        raise NotFoundError("Transform", transform_id)
    
    client = await get_dynamodb_client()
    
    await client.delete_item(
        TableName=TRANSFORMS_TABLE,
        Key={"transformId": {"S": transform_id}},
    )


async def execute_transform(transform_id: str, user_id: str) -> TransformExecution:
    """Transformを実行"""
    transform = await get_transform(transform_id)
    if not transform:
        raise NotFoundError("Transform", transform_id)
    
    # 実行履歴を作成
    execution_id = f"exec_{uuid.uuid4().hex[:12]}"
    now = int(datetime.utcnow().timestamp())
    
    execution_data = {
        "executionId": execution_id,
        "transformId": transform_id,
        "status": "pending",
        "startedAt": now,
    }
    
    client = await get_dynamodb_client()
    await client.put_item(
        TableName=EXECUTIONS_TABLE,
        Item=_dict_to_dynamodb_item(execution_data),
    )
    
    # Executorサービスを呼び出す（Phase 6で実装）
    # 現時点ではダミー実装
    raise NotImplementedError("Transform execution will be implemented in Phase 6 (Executor)")


async def list_transform_executions(
    transform_id: str,
    limit: int = 20,
    offset: int = 0,
) -> Tuple[List[TransformExecution], int]:
    """Transform実行履歴を取得"""
    client = await get_dynamodb_client()
    
    # GSIを使用してtransformIdでクエリ
    response = await client.query(
        TableName=EXECUTIONS_TABLE,
        IndexName="ExecutionsByTransform",
        KeyConditionExpression="transformId = :transformId",
        ExpressionAttributeValues={
            ":transformId": {"S": transform_id}
        },
        Limit=limit + offset,
        ScanIndexForward=False,  # 新しい順
    )
    
    items = response.get("Items", [])
    executions = []
    
    for item in items:
        finished_at = None
        if "finishedAt" in item and "N" in item["finishedAt"]:
            finished_at = datetime.fromtimestamp(int(item["finishedAt"]["N"]))
        
        error_message = None
        if "errorMessage" in item and "S" in item["errorMessage"]:
            error_message = item["errorMessage"]["S"]
        
        output_dataset_id = None
        if "outputDatasetId" in item and "S" in item["outputDatasetId"]:
            output_dataset_id = item["outputDatasetId"]["S"]
        
        executions.append(TransformExecution(
            execution_id=item["executionId"]["S"],
            transform_id=item["transformId"]["S"],
            status=item["status"]["S"],
            started_at=datetime.fromtimestamp(int(item["startedAt"]["N"])),
            finished_at=finished_at,
            error_message=error_message,
            output_dataset_id=output_dataset_id,
        ))
    
    total = len(executions)
    return executions[offset:offset+limit], total
