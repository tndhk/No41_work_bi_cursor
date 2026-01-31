"""Transforms APIルート - TDD実装中"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, status, Path
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError, ForbiddenError, ExecutionError
from app.services.transform_service import (
    list_transforms,
    create_transform,
    get_transform,
    update_transform,
    delete_transform,
    execute_transform,
    list_transform_executions,
)
from app.models.transform import Transform, TransformCreate, TransformUpdate, TransformExecution

router = APIRouter(prefix="/transforms", tags=["transforms"])


class TransformResponse(BaseModel):
    transform_id: str
    name: str
    owner_id: str
    code: str
    input_dataset_ids: list[str]
    output_dataset_id: Optional[str]
    params: dict
    schedule: Optional[str]
    created_at: str
    updated_at: str
    last_executed_at: Optional[str]


class TransformCreateRequest(BaseModel):
    name: str
    code: str
    input_dataset_ids: list[str]
    params: dict = {}
    schedule: Optional[str] = None


class TransformUpdateRequest(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    input_dataset_ids: Optional[list[str]] = None
    params: Optional[dict] = None
    schedule: Optional[str] = None


class TransformExecutionResponse(BaseModel):
    execution_id: str
    transform_id: str
    status: str
    started_at: str
    finished_at: Optional[str]
    error_message: Optional[str]
    output_dataset_id: Optional[str]


@router.get("", response_model=dict)
async def list_transforms_endpoint(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Transform一覧取得"""
    user_id = current_user["user_id"]
    transforms, total = await list_transforms(owner_id=user_id, limit=limit, offset=offset, q=q)
    
    return {
        "data": [
            TransformResponse(
                transform_id=t.transform_id,
                name=t.name,
                owner_id=t.owner_id,
                code=t.code,
                input_dataset_ids=t.input_dataset_ids,
                output_dataset_id=t.output_dataset_id,
                params=t.params,
                schedule=t.schedule,
                created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat(),
                last_executed_at=t.last_executed_at.isoformat() if t.last_executed_at else None,
            )
            for t in transforms
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
        },
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_transform_endpoint(
    request: TransformCreateRequest,
    current_user: dict = Depends(get_current_user),
):
    """Transform作成"""
    user_id = current_user["user_id"]
    transform_data = TransformCreate(
        name=request.name,
        code=request.code,
        input_dataset_ids=request.input_dataset_ids,
        params=request.params,
        schedule=request.schedule,
    )
    
    transform = await create_transform(user_id, transform_data)
    
    return {
        "data": TransformResponse(
            transform_id=transform.transform_id,
            name=transform.name,
            owner_id=transform.owner_id,
            code=transform.code,
            input_dataset_ids=transform.input_dataset_ids,
            output_dataset_id=transform.output_dataset_id,
            params=transform.params,
            schedule=transform.schedule,
            created_at=transform.created_at.isoformat(),
            updated_at=transform.updated_at.isoformat(),
            last_executed_at=transform.last_executed_at.isoformat() if transform.last_executed_at else None,
        )
    }


@router.get("/{transform_id}", response_model=dict)
async def get_transform_endpoint(
    transform_id: str = Path(..., description="Transform ID"),
    current_user: dict = Depends(get_current_user),
):
    """Transform詳細取得"""
    transform = await get_transform(transform_id)
    if not transform:
        raise NotFoundError("Transform", transform_id)
    
    return {
        "data": TransformResponse(
            transform_id=transform.transform_id,
            name=transform.name,
            owner_id=transform.owner_id,
            code=transform.code,
            input_dataset_ids=transform.input_dataset_ids,
            output_dataset_id=transform.output_dataset_id,
            params=transform.params,
            schedule=transform.schedule,
            created_at=transform.created_at.isoformat(),
            updated_at=transform.updated_at.isoformat(),
            last_executed_at=transform.last_executed_at.isoformat() if transform.last_executed_at else None,
        )
    }


@router.put("/{transform_id}", response_model=dict)
async def update_transform_endpoint(
    transform_id: str = Path(..., description="Transform ID"),
    request: TransformUpdateRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """Transform更新"""
    transform = await get_transform(transform_id)
    if not transform:
        raise NotFoundError("Transform", transform_id)
    
    # 所有者チェック
    if transform.owner_id != current_user["user_id"]:
        raise ForbiddenError("You don't have permission to update this transform")
    
    transform_data = TransformUpdate(
        name=request.name,
        code=request.code,
        input_dataset_ids=request.input_dataset_ids,
        params=request.params,
        schedule=request.schedule,
    )
    
    transform = await update_transform(transform_id, transform_data)
    
    return {
        "data": TransformResponse(
            transform_id=transform.transform_id,
            name=transform.name,
            owner_id=transform.owner_id,
            code=transform.code,
            input_dataset_ids=transform.input_dataset_ids,
            output_dataset_id=transform.output_dataset_id,
            params=transform.params,
            schedule=transform.schedule,
            created_at=transform.created_at.isoformat(),
            updated_at=transform.updated_at.isoformat(),
            last_executed_at=transform.last_executed_at.isoformat() if transform.last_executed_at else None,
        )
    }


@router.delete("/{transform_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_transform_endpoint(
    transform_id: str = Path(..., description="Transform ID"),
    current_user: dict = Depends(get_current_user),
):
    """Transform削除"""
    transform = await get_transform(transform_id)
    if not transform:
        raise NotFoundError("Transform", transform_id)
    
    # 所有者チェック
    if transform.owner_id != current_user["user_id"]:
        raise ForbiddenError("You don't have permission to delete this transform")
    
    await delete_transform(transform_id)


@router.post("/{transform_id}/execute", response_model=dict)
async def execute_transform_endpoint(
    transform_id: str = Path(..., description="Transform ID"),
    current_user: dict = Depends(get_current_user),
):
    """Transform手動実行"""
    transform = await get_transform(transform_id)
    if not transform:
        raise NotFoundError("Transform", transform_id)
    
    try:
        execution = await execute_transform(transform_id, current_user["user_id"])
    except NotImplementedError:
        raise ExecutionError("Transform execution will be implemented in Phase 6 (Executor)")
    except Exception as e:
        raise ExecutionError(str(e))
    
    return {
        "data": TransformExecutionResponse(
            execution_id=execution.execution_id,
            transform_id=execution.transform_id,
            status=execution.status,
            started_at=execution.started_at.isoformat(),
            finished_at=execution.finished_at.isoformat() if execution.finished_at else None,
            error_message=execution.error_message,
            output_dataset_id=execution.output_dataset_id,
        )
    }


@router.get("/{transform_id}/executions", response_model=dict)
async def list_executions_endpoint(
    transform_id: str = Path(..., description="Transform ID"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Transform実行履歴取得"""
    transform = await get_transform(transform_id)
    if not transform:
        raise NotFoundError("Transform", transform_id)
    
    executions, total = await list_transform_executions(transform_id, limit=limit, offset=offset)
    
    return {
        "data": [
            TransformExecutionResponse(
                execution_id=e.execution_id,
                transform_id=e.transform_id,
                status=e.status,
                started_at=e.started_at.isoformat(),
                finished_at=e.finished_at.isoformat() if e.finished_at else None,
                error_message=e.error_message,
                output_dataset_id=e.output_dataset_id,
            )
            for e in executions
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
        },
    }
