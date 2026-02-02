"""Cardモデル"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class CardBase(BaseModel):
    name: str
    dataset_id: str
    code: str


class CardCreate(CardBase):
    params: Dict[str, Any] = {}
    used_columns: List[str] = []
    filter_applicable: List[str] = []


class CardUpdate(BaseModel):
    name: Optional[str] = None
    dataset_id: Optional[str] = None
    code: Optional[str] = None
    params: Optional[Dict[str, Any]] = None
    used_columns: Optional[List[str]] = None
    filter_applicable: Optional[List[str]] = None


class Card(CardBase):
    card_id: str
    owner_id: str
    params: Dict[str, Any]
    used_columns: List[str]
    filter_applicable: List[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class CardPreviewRequest(BaseModel):
    filters: Dict[str, Any] = {}
    params: Dict[str, Any] = {}


class CardPreviewResponse(BaseModel):
    html: str
    used_columns: List[str]
    filter_applicable: List[str]
