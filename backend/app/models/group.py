"""Groupモデル"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel


class GroupBase(BaseModel):
    name: str


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = None


class Group(GroupBase):
    group_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class GroupMember(BaseModel):
    group_id: str
    user_id: str
    added_at: datetime


class GroupDetail(Group):
    members: List[dict] = []
