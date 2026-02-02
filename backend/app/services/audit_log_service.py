"""Audit Logサービス"""
from datetime import datetime
from typing import Optional, List, Dict, Any
import uuid

from app.db.dynamodb import get_dynamodb_client, get_table_name
from app.models.audit_log import AuditLog, AuditLogCreate
from app.core.logging import get_logger


AUDIT_LOGS_TABLE = get_table_name("AuditLogs")
logger = get_logger(__name__)


def _item_to_audit_log(item: dict) -> AuditLog:
    """DynamoDBアイテムをAuditLogモデルに変換"""
    details = {}
    if "details" in item and "M" in item["details"]:
        details = _parse_map_attribute(item["details"])
    
    return AuditLog(
        log_id=item["logId"]["S"],
        timestamp=datetime.fromtimestamp(int(item["timestamp"]["N"]) / 1000),
        event_type=item["eventType"]["S"],
        user_id=item["userId"]["S"],
        target_type=item["targetType"]["S"],
        target_id=item["targetId"]["S"],
        details=details,
        request_id=item.get("requestId", {}).get("S") if "requestId" in item else None,
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
        elif isinstance(value, bool):
            item[key] = {"BOOL": value}
        elif isinstance(value, (int, float)):
            item[key] = {"N": str(value)}
        elif isinstance(value, dict):
            item[key] = {"M": _dict_to_dynamodb_item(value)}
        elif isinstance(value, list):
            list_items = []
            for v in value:
                if isinstance(v, dict):
                    list_items.append({"M": _dict_to_dynamodb_item(v)})
                elif isinstance(v, bool):
                    list_items.append({"BOOL": v})
                elif isinstance(v, (int, float)):
                    list_items.append({"N": str(v)})
                else:
                    list_items.append({"S": str(v)})
            item[key] = {"L": list_items}
        elif value is None:
            continue
        else:
            item[key] = {"S": str(value)}
    return item


async def create_audit_log(
    event_type: str,
    user_id: str,
    target_type: str,
    target_id: str,
    details: Dict[str, Any] = None,
    request_id: Optional[str] = None,
) -> Optional[AuditLog]:
    """
    監査ログを作成
    
    Note: 監査ログ記録が失敗しても例外を発生させません。
    エラーはログに記録され、Noneを返します。
    """
    log_id = f"log_{uuid.uuid4().hex[:12]}"
    timestamp_ms = int(datetime.utcnow().timestamp() * 1000)
    log_details = details or {}
    
    item_data = {
        "logId": log_id,
        "timestamp": timestamp_ms,
        "eventType": event_type,
        "userId": user_id,
        "targetType": target_type,
        "targetId": target_id,
        "details": log_details,
    }
    
    if request_id:
        item_data["requestId"] = request_id
    
    try:
        client = await get_dynamodb_client()
        await client.put_item(
            TableName=AUDIT_LOGS_TABLE,
            Item=_dict_to_dynamodb_item(item_data),
        )
        
        return AuditLog(
            log_id=log_id,
            timestamp=datetime.fromtimestamp(timestamp_ms / 1000),
            event_type=event_type,
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            details=log_details,
            request_id=request_id,
        )
    except Exception as e:
        # 監査ログ記録失敗はAPIレスポンスに影響させない
        logger.error(
            "Failed to create audit log",
            event_type=event_type,
            user_id=user_id,
            target_type=target_type,
            target_id=target_id,
            request_id=request_id,
            error=str(e),
            exc_info=True,
        )
        return None


async def query_audit_logs_by_target(
    target_id: str,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    event_type: Optional[str] = None,
    limit: int = 100,
) -> List[AuditLog]:
    """
    対象IDで監査ログを検索（LogsByTarget GSI使用）
    
    Note: 総件数の取得には別途Countクエリが必要ですが、
    パフォーマンスを考慮して返却件数のみを返します。
    """
    try:
        client = await get_dynamodb_client()
        
        key_condition = "targetId = :targetId"
        expression_values = {
            ":targetId": {"S": target_id}
        }
        
        # タイムスタンプ範囲フィルタ
        if start_time:
            expression_values[":startTime"] = {"N": str(int(start_time.timestamp() * 1000))}
            if end_time:
                expression_values[":endTime"] = {"N": str(int(end_time.timestamp() * 1000))}
                key_condition += " AND timestamp BETWEEN :startTime AND :endTime"
            else:
                key_condition += " AND timestamp >= :startTime"
        elif end_time:
            expression_values[":endTime"] = {"N": str(int(end_time.timestamp() * 1000))}
            key_condition += " AND timestamp <= :endTime"
        
        # イベントタイプフィルタ
        filter_expression = None
        if event_type:
            expression_values[":eventType"] = {"S": event_type}
            filter_expression = "eventType = :eventType"
        
        query_params = {
            "TableName": AUDIT_LOGS_TABLE,
            "IndexName": "LogsByTarget",
            "KeyConditionExpression": key_condition,
            "ExpressionAttributeValues": expression_values,
            "Limit": limit,
            "ScanIndexForward": False,  # 新しい順
        }
        
        if filter_expression:
            query_params["FilterExpression"] = filter_expression
        
        response = await client.query(**query_params)
        
        return [_item_to_audit_log(item) for item in response.get("Items", [])]
    except Exception as e:
        logger.error(
            "Failed to query audit logs",
            target_id=target_id,
            error=str(e),
            exc_info=True,
        )
        # エラー時は空リストを返す（APIレスポンスに影響させない）
        return []
