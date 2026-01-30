"""ヘルスチェックエンドポイントのテスト"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_endpoint(client):
    """ヘルスチェックエンドポイントが正常に動作する"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


def test_health_endpoint_returns_timestamp(client):
    """ヘルスチェックエンドポイントがタイムスタンプを返す"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "timestamp" in data
