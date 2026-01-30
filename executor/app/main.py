"""Executor エントリポイント"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

from app.runner import execute_card as run_card, execute_transform as run_transform, ExecutionError

app = FastAPI(
    title="BI Executor",
    description="Python実行基盤（Card/Transform実行）",
    version="0.1.0",
)


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
        result = await run_card(
            code=request.code,
            dataset_path=request.dataset_path,
            filters=request.filters,
            params=request.params,
        )
        return {"status": "success", "data": result}
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/execute/transform")
async def execute_transform_endpoint(request: TransformExecuteRequest):
    """Transform実行"""
    try:
        result = await run_transform(
            code=request.code,
            input_dataset_paths=request.input_dataset_paths,
        )
        # DataFrameはシリアライズできないので、メタデータのみ返す
        return {
            "status": "success",
            "data": {
                "row_count": result["row_count"],
                "column_count": result["column_count"],
                "columns": result["columns"],
            }
        }
    except ExecutionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")
