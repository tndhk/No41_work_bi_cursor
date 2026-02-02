"""Audit Logs APIルート"""
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, Query, HTTPException, status

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError, ForbiddenError
from app.services.audit_log_service import query_audit_logs_by_target
from app.services.dashboard_service import get_dashboard
from app.models.audit_log import AuditLog

router = APIRouter(prefix="/audit-logs", tags=["audit-logs"])


def _parse_iso_datetime(time_str: str) -> datetime:
    """ISO 8601形式の文字列をdatetimeに変換"""
    normalized = time_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        # タイムゾーン情報がない場合はUTCとして扱う
        try:
            dt = datetime.fromisoformat(time_str)
            return dt.replace(tzinfo=timezone.utc)
        except ValueError:
            raise ValueError(f"Invalid datetime format: {time_str}")


def _audit_log_to_dict(log: AuditLog) -> Dict[str, Any]:
    """AuditLogモデルを辞書に変換"""
    return {
        "log_id": log.log_id,
        "timestamp": log.timestamp.isoformat(),
        "event_type": log.event_type,
        "user_id": log.user_id,
        "target_type": log.target_type,
        "target_id": log.target_id,
        "details": log.details,
        "request_id": log.request_id,
    }


@router.get("", response_model=dict)
async def list_audit_logs(
    dashboard_id: Optional[str] = Query(None, description="Dashboard ID（必須）"),
    start_time: Optional[str] = Query(None, description="開始時刻（ISO 8601形式）"),
    end_time: Optional[str] = Query(None, description="終了時刻（ISO 8601形式）"),
    event_type: Optional[str] = Query(None, description="イベントタイプ"),
    limit: int = Query(100, ge=1, le=1000, description="取得件数"),
    current_user: dict = Depends(get_current_user),
):
    """監査ログ一覧取得（Dashboardオーナーのみ）"""
    if not dashboard_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="dashboard_id is required",
        )
    
    # Dashboardの存在確認とオーナーチェック
    dashboard = await get_dashboard(dashboard_id)
    if not dashboard:
        raise NotFoundError("Dashboard", dashboard_id)
    
    user_id = current_user["user_id"]
    if dashboard.owner_id != user_id:
        raise ForbiddenError("You don't have permission to view audit logs for this dashboard")
    
    # 時刻パース
    start_dt = None
    end_dt = None
    if start_time:
        try:
            start_dt = _parse_iso_datetime(start_time)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid start_time format. Use ISO 8601 format.",
            )
    if end_time:
        try:
            end_dt = _parse_iso_datetime(end_time)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid end_time format. Use ISO 8601 format.",
            )
    
    # 監査ログを検索（target_idにdashboard_idを使用）
    logs = await query_audit_logs_by_target(
        target_id=dashboard_id,
        start_time=start_dt,
        end_time=end_dt,
        event_type=event_type,
        limit=limit,
    )
    
    # 実際の総件数は取得できないため、返却件数を表示
    # 将来的にCountを取得する場合は、別途クエリが必要
    return {
        "data": [_audit_log_to_dict(log) for log in logs],
        "pagination": {
            "total": len(logs),  # 実際の総件数は取得不可（GSI制約）
            "limit": limit,
            "has_more": len(logs) == limit,  # 追加データがある可能性を示す
        },
    }
