"""Dashboardモデル"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict


class DashboardBase(BaseModel):
    name: str


class DashboardCreate(DashboardBase):
    layout: Dict[str, Any] = {}
    filters: List[Dict[str, Any]] = []
    default_filter_view_id: Optional[str] = None


class DashboardUpdate(BaseModel):
    name: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    filters: Optional[List[Dict[str, Any]]] = None
    default_filter_view_id: Optional[str] = None


class Dashboard(DashboardBase):
    dashboard_id: str
    owner_id: str
    layout: Dict[str, Any]
    filters: List[Dict[str, Any]]
    default_filter_view_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class DashboardShare(BaseModel):
    share_id: str
    dashboard_id: str
    shared_to_type: str  # "user" | "group"
    shared_to_id: str
    permission: str  # "owner" | "editor" | "viewer"
    shared_by: str
    created_at: datetime


class FilterView(BaseModel):
    filter_view_id: str
    dashboard_id: str
    name: str
    owner_id: str
    filter_state: Dict[str, Any]
    is_shared: bool
    is_default: bool
    created_at: datetime
    updated_at: datetime
