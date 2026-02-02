"""Audit Logモデル"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class AuditLogBase(BaseModel):
    event_type: str
    user_id: str  # ログイン失敗時は "unknown" を使用
    target_type: str
    target_id: str  # ログイン失敗時は "unknown" を使用
    details: Dict[str, Any] = {}
    request_id: Optional[str] = None


class AuditLogCreate(AuditLogBase):
    """監査ログ作成用モデル"""
    pass


class AuditLog(AuditLogBase):
    """監査ログモデル"""
    log_id: str
    timestamp: datetime
    
    model_config = ConfigDict(from_attributes=True)


class AuditLogQuery(BaseModel):
    """監査ログ検索用モデル"""
    dashboard_id: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    event_type: Optional[str] = None
    limit: int = 100
