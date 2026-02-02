"""FastAPI アプリケーションエントリポイント"""
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.core.config import settings
from app.core.logging import setup_logging
from app.core.middleware import RequestIDMiddleware
from app.core.exceptions import BIException
from app.api.routes import auth, users, chatbot
from app.db.dynamodb import close_dynamodb
from app.db.s3 import close_s3

# ログ設定初期化
setup_logging()

app = FastAPI(
    title="社内BI・Pythonカード API",
    description="ローカルCSVおよびS3上のCSVを取り込み、PythonでHTMLカードを定義してダッシュボードに配置できる社内BIツール",
    version="0.1.0",
)

# ミドルウェア登録
app.add_middleware(RequestIDMiddleware)


def _get_request_id(request: Request) -> str | None:
    """リクエストIDを取得"""
    return getattr(request.state, "request_id", None)


def _create_error_response(
    status_code: int,
    error: dict,
    request: Request,
) -> JSONResponse:
    """エラーレスポンスを作成"""
    request_id = _get_request_id(request)
    meta = {"request_id": request_id} if request_id else {}
    
    return JSONResponse(
        status_code=status_code,
        content={
            "error": error,
            "meta": meta,
        },
    )


@app.exception_handler(BIException)
async def bi_exception_handler(request: Request, exc: BIException):
    """BI例外ハンドラー"""
    error = exc.detail if isinstance(exc.detail, dict) else {"message": str(exc.detail)}
    return _create_error_response(exc.status_code, error, request)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """バリデーションエラーハンドラー"""
    error = {
        "code": "VALIDATION_ERROR",
        "message": "Validation error",
        "details": exc.errors(),
    }
    return _create_error_response(422, error, request)


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """一般例外ハンドラー"""
    error = {
        "code": "INTERNAL_ERROR",
        "message": "Internal server error",
    }
    return _create_error_response(500, error, request)


# ルーター登録
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(chatbot.router, prefix="/api")

# Groups API
from app.api.routes import groups
app.include_router(groups.router, prefix="/api")

# Datasets API
from app.api.routes import datasets
app.include_router(datasets.router, prefix="/api")

# Cards API
from app.api.routes import cards
app.include_router(cards.router, prefix="/api")

# Dashboards API
from app.api.routes import dashboards, dashboard_shares, filter_views
app.include_router(dashboards.router, prefix="/api")
app.include_router(dashboard_shares.router, prefix="/api")
app.include_router(filter_views.router, prefix="/api")

# Transforms API
from app.api.routes import transforms
app.include_router(transforms.router, prefix="/api")

# Audit Logs API
from app.api.routes import audit_logs
app.include_router(audit_logs.router, prefix="/api")

# Test setup API (テスト環境のみ)
if settings.allow_test_setup:
    from app.api.routes import test_setup
    app.include_router(test_setup.router, prefix="/api")


@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時に接続を閉じる"""
    await close_dynamodb()
    await close_s3()


@app.get("/health")
async def health():
    """ヘルスチェックエンドポイント"""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_debug,
    )
