"""Transformモデル - TDD実装中"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class TransformBase(BaseModel):
    name: str
    code: str


class TransformCreate(TransformBase):
    input_dataset_ids: List[str]
    params: Dict[str, Any] = {}
    schedule: Optional[str] = None


class TransformUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    input_dataset_ids: Optional[List[str]] = None
    params: Optional[Dict[str, Any]] = None
    schedule: Optional[str] = None


class Transform(BaseModel):
    transform_id: str
    name: str
    owner_id: str
    code: str
    input_dataset_ids: List[str]
    output_dataset_id: Optional[str] = None
    params: Dict[str, Any] = {}
    schedule: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_executed_at: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class TransformExecution(BaseModel):
    execution_id: str
    transform_id: str
    status: str  # pending | running | completed | failed
    started_at: datetime
    finished_at: Optional[datetime] = None
    error_message: Optional[str] = None
    output_dataset_id: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)
