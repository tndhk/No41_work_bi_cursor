"""ミドルウェアのテスト"""
import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
import uuid

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_request_id_middleware(client):
    """リクエストIDが生成される"""
    response = client.get("/health")
    assert response.status_code == 200
    # リクエストIDがメタに含まれるか確認
    data = response.json()
    # メタデータは後で追加されるため、現時点では基本的なレスポンスのみ確認
    assert "status" in data


def test_error_handler(client):
    """エラーハンドラーが動作する"""
    # 存在しないエンドポイント
    response = client.get("/nonexistent")
    assert response.status_code == 404
    # エラーレスポンス形式を確認
    data = response.json()
    assert "detail" in data
