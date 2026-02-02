"""Datasets APIルート"""
from typing import Optional
from fastapi import APIRouter, Depends, status, Query, Path, UploadFile, File, Form
from pydantic import BaseModel

from app.api.deps import get_current_user
from app.core.exceptions import NotFoundError, ForbiddenError, BadRequestError
from app.services.dataset_service import (
    create_dataset_from_local_csv,
    create_dataset_from_s3_csv,
    get_dataset,
    list_datasets,
    update_dataset,
    delete_dataset,
    reimport_dataset,
    get_dataset_preview,
)
from app.models.dataset import Dataset, DatasetUpdate, DatasetPreview

router = APIRouter(prefix="/datasets", tags=["datasets"])


class DatasetResponse(BaseModel):
    dataset_id: str
    name: str
    owner_id: str
    source_type: str
    source_config: dict
    schema: list
    row_count: int
    column_count: int
    s3_path: str
    partition_column: Optional[str]
    created_at: str
    updated_at: str
    last_import_at: Optional[str]
    last_import_by: Optional[str]


class DatasetCreateRequest(BaseModel):
    name: str
    encoding: str = "utf-8"
    delimiter: str = ","
    has_header: bool = True


class DatasetUpdateRequest(BaseModel):
    name: Optional[str] = None


class S3ImportRequest(BaseModel):
    name: str
    bucket: str
    key: str
    encoding: str = "utf-8"
    delimiter: str = ","
    has_header: bool = True


@router.get("", response_model=dict)
async def list_datasets_endpoint(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    q: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """Dataset一覧取得"""
    user_id = current_user["user_id"]
    datasets, total = await list_datasets(owner_id=user_id, limit=limit, offset=offset, q=q)
    
    return {
        "data": [
            DatasetResponse(
                dataset_id=d.dataset_id,
                name=d.name,
                owner_id=d.owner_id,
                source_type=d.source_type,
                source_config=d.source_config,
                schema=[{"name": col.name, "dtype": col.dtype, "nullable": col.nullable} for col in d.schema],
                row_count=d.row_count,
                column_count=d.column_count,
                s3_path=d.s3_path,
                partition_column=d.partition_column,
                created_at=d.created_at.isoformat(),
                updated_at=d.updated_at.isoformat(),
                last_import_at=d.last_import_at.isoformat() if d.last_import_at else None,
                last_import_by=d.last_import_by,
            )
            for d in datasets
        ],
        "pagination": {
            "total": total,
            "limit": limit,
            "offset": offset,
            "has_next": offset + limit < total,
        },
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_dataset_endpoint(
    name: str = Form(...),
    file: UploadFile = File(...),
    encoding: str = Form("utf-8"),
    delimiter: str = Form(","),
    has_header: bool = Form(True),
    current_user: dict = Depends(get_current_user),
):
    """Dataset作成（Local CSV取り込み）"""
    user_id = current_user["user_id"]
    
    # ファイルを読み込む
    csv_content = await file.read()
    
    try:
        dataset = await create_dataset_from_local_csv(
            user_id=user_id,
            name=name,
            csv_content=csv_content,
            encoding=encoding,
            delimiter=delimiter,
            has_header=has_header,
        )
    except ValueError as e:
        raise BadRequestError(str(e))
    
    return {
        "data": DatasetResponse(
            dataset_id=dataset.dataset_id,
            name=dataset.name,
            owner_id=dataset.owner_id,
            source_type=dataset.source_type,
            source_config=dataset.source_config,
            schema=[{"name": col.name, "dtype": col.dtype, "nullable": col.nullable} for col in dataset.schema],
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            s3_path=dataset.s3_path,
            partition_column=dataset.partition_column,
            created_at=dataset.created_at.isoformat(),
            updated_at=dataset.updated_at.isoformat(),
            last_import_at=dataset.last_import_at.isoformat() if dataset.last_import_at else None,
            last_import_by=dataset.last_import_by,
        )
    }


@router.post("/s3-import", response_model=dict, status_code=status.HTTP_201_CREATED)
async def s3_import_dataset_endpoint(
    request: S3ImportRequest,
    current_user: dict = Depends(get_current_user),
):
    """S3 CSV取り込み"""
    user_id = current_user["user_id"]
    
    try:
        dataset = await create_dataset_from_s3_csv(
            user_id=user_id,
            name=request.name,
            bucket=request.bucket,
            key=request.key,
            encoding=request.encoding,
            delimiter=request.delimiter,
            has_header=request.has_header,
        )
    except ValueError as e:
        raise BadRequestError(str(e))
    
    return {
        "data": DatasetResponse(
            dataset_id=dataset.dataset_id,
            name=dataset.name,
            owner_id=dataset.owner_id,
            source_type=dataset.source_type,
            source_config=dataset.source_config,
            schema=[{"name": col.name, "dtype": col.dtype, "nullable": col.nullable} for col in dataset.schema],
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            s3_path=dataset.s3_path,
            partition_column=dataset.partition_column,
            created_at=dataset.created_at.isoformat(),
            updated_at=dataset.updated_at.isoformat(),
            last_import_at=dataset.last_import_at.isoformat() if dataset.last_import_at else None,
            last_import_by=dataset.last_import_by,
        )
    }


@router.get("/{dataset_id}", response_model=dict)
async def get_dataset_endpoint(
    dataset_id: str = Path(..., description="Dataset ID"),
    current_user: dict = Depends(get_current_user),
):
    """Dataset詳細取得"""
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    
    return {
        "data": DatasetResponse(
            dataset_id=dataset.dataset_id,
            name=dataset.name,
            owner_id=dataset.owner_id,
            source_type=dataset.source_type,
            source_config=dataset.source_config,
            schema=[{"name": col.name, "dtype": col.dtype, "nullable": col.nullable} for col in dataset.schema],
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            s3_path=dataset.s3_path,
            partition_column=dataset.partition_column,
            created_at=dataset.created_at.isoformat(),
            updated_at=dataset.updated_at.isoformat(),
            last_import_at=dataset.last_import_at.isoformat() if dataset.last_import_at else None,
            last_import_by=dataset.last_import_by,
        )
    }


@router.put("/{dataset_id}", response_model=dict)
async def update_dataset_endpoint(
    dataset_id: str = Path(..., description="Dataset ID"),
    request: DatasetUpdateRequest = ...,
    current_user: dict = Depends(get_current_user),
):
    """Dataset更新"""
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    
    # 所有者チェック
    if dataset.owner_id != current_user["user_id"]:
        raise ForbiddenError("You don't have permission to update this dataset")
    
    dataset_data = DatasetUpdate(name=request.name)
    dataset = await update_dataset(dataset_id, dataset_data)
    
    return {
        "data": DatasetResponse(
            dataset_id=dataset.dataset_id,
            name=dataset.name,
            owner_id=dataset.owner_id,
            source_type=dataset.source_type,
            source_config=dataset.source_config,
            schema=[{"name": col.name, "dtype": col.dtype, "nullable": col.nullable} for col in dataset.schema],
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            s3_path=dataset.s3_path,
            partition_column=dataset.partition_column,
            created_at=dataset.created_at.isoformat(),
            updated_at=dataset.updated_at.isoformat(),
            last_import_at=dataset.last_import_at.isoformat() if dataset.last_import_at else None,
            last_import_by=dataset.last_import_by,
        )
    }


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset_endpoint(
    dataset_id: str = Path(..., description="Dataset ID"),
    current_user: dict = Depends(get_current_user),
):
    """Dataset削除"""
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    
    # 所有者チェック
    if dataset.owner_id != current_user["user_id"]:
        raise ForbiddenError("You don't have permission to delete this dataset")
    
    await delete_dataset(dataset_id)


@router.post("/{dataset_id}/import", response_model=dict)
async def reimport_dataset_endpoint(
    dataset_id: str = Path(..., description="Dataset ID"),
    current_user: dict = Depends(get_current_user),
):
    """Dataset再取り込み"""
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    
    # 所有者チェック
    if dataset.owner_id != current_user["user_id"]:
        raise ForbiddenError("You don't have permission to reimport this dataset")
    
    try:
        dataset = await reimport_dataset(dataset_id, current_user["user_id"])
    except ValueError as e:
        raise BadRequestError(str(e))
    
    return {
        "data": DatasetResponse(
            dataset_id=dataset.dataset_id,
            name=dataset.name,
            owner_id=dataset.owner_id,
            source_type=dataset.source_type,
            source_config=dataset.source_config,
            schema=[{"name": col.name, "dtype": col.dtype, "nullable": col.nullable} for col in dataset.schema],
            row_count=dataset.row_count,
            column_count=dataset.column_count,
            s3_path=dataset.s3_path,
            partition_column=dataset.partition_column,
            created_at=dataset.created_at.isoformat(),
            updated_at=dataset.updated_at.isoformat(),
            last_import_at=dataset.last_import_at.isoformat() if dataset.last_import_at else None,
            last_import_by=dataset.last_import_by,
        ),
        "schema_changed": dataset.source_config.get("schema_changed", False),
    }


@router.get("/{dataset_id}/preview", response_model=dict)
async def get_dataset_preview_endpoint(
    dataset_id: str = Path(..., description="Dataset ID"),
    limit: int = Query(100, ge=1, le=1000),
    current_user: dict = Depends(get_current_user),
):
    """Datasetプレビュー取得"""
    dataset = await get_dataset(dataset_id)
    if not dataset:
        raise NotFoundError("Dataset", dataset_id)
    
    try:
        preview = await get_dataset_preview(dataset_id, limit=limit)
    except ValueError as e:
        raise BadRequestError(str(e))
    
    return {
        "data": preview.model_dump()
    }
