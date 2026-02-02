"""Datasetモデル"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class DatasetBase(BaseModel):
    name: str


class DatasetCreate(DatasetBase):
    source_type: str  # "local_csv" | "s3_csv" | "transform"
    source_config: Dict[str, Any]


class DatasetUpdate(BaseModel):
    name: Optional[str] = None


class ColumnSchema(BaseModel):
    name: str
    dtype: str
    nullable: bool = True


class Dataset(DatasetBase):
    dataset_id: str
    owner_id: str
    source_type: str
    source_config: Dict[str, Any]
    schema: List[ColumnSchema]
    row_count: int
    column_count: int
    s3_path: str
    partition_column: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    last_import_at: Optional[datetime] = None
    last_import_by: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class DatasetPreview(BaseModel):
    columns: List[str]
    rows: List[Dict[str, Any]]
    total_rows: int
