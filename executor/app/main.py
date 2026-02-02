"""Executor エントリポイント"""
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Dict, Any, Optional
import uuid

from app.runner import execute_card as run_card, execute_transform as run_transform, ExecutionError
from app.queue import ExecutionQueue, QueueFullError
from app.config import settings
from app.db import close_s3

app = FastAPI(
    title="BI Executor",
    description="Python実行基盤（Card/Transform実行）",
    version="0.1.0",
)

# 実行キューを初期化
card_queue = ExecutionQueue(
    max_concurrent=settings.max_concurrent_cards,
    queue_size=settings.queue_size_cards,
)
transform_queue = ExecutionQueue(
    max_concurrent=settings.max_concurrent_transforms,
    queue_size=settings.queue_size_transforms,
)


@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時にワーカーを開始"""
    card_queue.start()
    transform_queue.start()


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時にワーカーを停止し、接続を閉じる"""
    card_queue.stop()
    transform_queue.stop()
    await close_s3()


class CardExecuteRequest(BaseModel):
    code: str
    dataset_path: str
    filters: Dict[str, Any] = {}
    params: Dict[str, Any] = {}


class TransformExecuteRequest(BaseModel):
    code: str
    input_dataset_paths: Dict[str, str]


@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {"status": "ok"}


@app.post("/execute/card")
async def execute_card_endpoint(request: CardExecuteRequest):
    """Card実行"""
    try:
        # キューが満杯の場合は503を返す
        if card_queue.is_full():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Card execution queue is full. Please try again later."
            )
        
        task_id = f"card_{uuid.uuid4().hex[:12]}"
        
        async def execute():
            return await run_card(
                code=request.code,
                dataset_path=request.dataset_path,
                filters=request.filters,
                params=request.params,
            )
        
        await card_queue.submit(task_id, execute)
        
        # 実際の実装では、タスクの完了を待つ必要があるが、
        # ここでは簡略化してキューに追加するだけ
        result = await execute()
        return {"status": "success", "data": result}
    except QueueFullError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Card execution queue is full. Please try again later."
        )
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/execute/transform")
async def execute_transform_endpoint(request: TransformExecuteRequest):
    """Transform実行"""
    try:
        # キューが満杯の場合は503を返す
        if transform_queue.is_full():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Transform execution queue is full. Please try again later."
            )
        
        task_id = f"transform_{uuid.uuid4().hex[:12]}"
        
        async def execute():
            return await run_transform(
                code=request.code,
                input_dataset_paths=request.input_dataset_paths,
            )
        
        await transform_queue.submit(task_id, execute)
        
        # 実際の実装では、タスクの完了を待つ必要があるが、
        # ここでは簡略化してキューに追加するだけ
        result = await execute()
        
        # DataFrameはシリアライズできないので、メタデータのみ返す
        return {
            "status": "success",
            "data": {
                "row_count": result["row_count"],
                "column_count": result["column_count"],
                "columns": result["columns"],
            }
        }
    except QueueFullError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Transform execution queue is full. Please try again later."
        )
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
