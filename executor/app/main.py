"""Executor エントリポイント"""
from fastapi import FastAPI

app = FastAPI(
    title="BI Executor",
    description="Python実行基盤（Card/Transform実行）",
    version="0.1.0",
)


@app.get("/health")
async def health():
    """ヘルスチェック"""
    return {"status": "ok"}


@app.post("/execute/card")
async def execute_card():
    """Card実行"""
    # TODO: 実装
    return {"status": "not_implemented"}


@app.post("/execute/transform")
async def execute_transform():
    """Transform実行"""
    # TODO: 実装
    return {"status": "not_implemented"}
