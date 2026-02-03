"""Cache Serviceのテスト"""
import pytest
from datetime import datetime, timedelta
import json
from unittest.mock import patch

from app.services.cache_service import (
    InMemoryCacheBackend,
    generate_cache_key,
    get_cached_card_preview,
    set_cached_card_preview,
    invalidate_card_preview_cache,
    get_cache_backend,
)


@pytest.fixture
def in_memory_cache():
    """インメモリキャッシュバックエンドのフィクスチャ"""
    cache = InMemoryCacheBackend()
    yield cache
    cache.clear()


@pytest.mark.asyncio
async def test_in_memory_cache_get_set(in_memory_cache):
    """インメモリキャッシュの取得・設定テスト"""
    await in_memory_cache.set("test_key", "test_value", ttl_seconds=60)
    
    value = await in_memory_cache.get("test_key")
    assert value == "test_value"
    
    # 存在しないキー
    value = await in_memory_cache.get("nonexistent")
    assert value is None


@pytest.mark.asyncio
async def test_in_memory_cache_ttl(in_memory_cache):
    """インメモリキャッシュのTTLテスト"""
    await in_memory_cache.set("test_key", "test_value", ttl_seconds=1)
    
    # すぐに取得できる
    value = await in_memory_cache.get("test_key")
    assert value == "test_value"
    
    # 1秒以上待つと期限切れ
    import asyncio
    await asyncio.sleep(1.1)
    
    value = await in_memory_cache.get("test_key")
    assert value is None


@pytest.mark.asyncio
async def test_in_memory_cache_delete(in_memory_cache):
    """インメモリキャッシュの削除テスト"""
    await in_memory_cache.set("test_key", "test_value", ttl_seconds=60)
    
    value = await in_memory_cache.get("test_key")
    assert value == "test_value"
    
    await in_memory_cache.delete("test_key")
    
    value = await in_memory_cache.get("test_key")
    assert value is None


def test_generate_cache_key():
    """キャッシュキー生成テスト"""
    card_id = "card_test123"
    filters1 = {"category": "A", "date": "2024-01-01"}
    filters2 = {"date": "2024-01-01", "category": "A"}  # 順序が異なる
    params1 = {"limit": 10, "mode": "summary"}
    params2 = {"mode": "summary", "limit": 10}  # 順序が異なる
    
    key1 = generate_cache_key(card_id, filters1, params1)
    key2 = generate_cache_key(card_id, filters2, params2)
    
    # 順序が異なっても同じキーが生成される
    assert key1 == key2
    assert key1.startswith("card_preview:")
    assert card_id in key1
    
    # 異なるフィルタ値では異なるキー
    filters3 = {"category": "B", "date": "2024-01-01"}
    key3 = generate_cache_key(card_id, filters3, params1)
    assert key1 != key3

    # paramsが異なる場合はキーが変わる
    params3 = {"limit": 5, "mode": "summary"}
    key4 = generate_cache_key(card_id, filters1, params3)
    assert key1 != key4


@pytest.mark.asyncio
async def test_get_cached_card_preview_miss(in_memory_cache):
    """キャッシュミスのテスト"""
    with patch('app.services.cache_service.get_cache_backend', return_value=in_memory_cache):
        preview = await get_cached_card_preview("card_test123", {"category": "A"}, {})
        assert preview is None


@pytest.mark.asyncio
async def test_set_and_get_cached_card_preview(in_memory_cache):
    """キャッシュの設定と取得テスト"""
    card_id = "card_test123"
    filters = {"category": "A", "date": "2024-01-01"}
    params = {"limit": 10}
    preview_data = {
        "html": "<div>Test HTML</div>",
        "used_columns": ["col1", "col2"],
        "filter_applicable": ["category"],
    }
    
    with patch('app.services.cache_service.get_cache_backend', return_value=in_memory_cache):
        # キャッシュに保存
        await set_cached_card_preview(card_id, filters, params, preview_data, ttl_seconds=60)
        
        # キャッシュから取得
        cached = await get_cached_card_preview(card_id, filters, params)
        assert cached is not None
        assert cached["html"] == preview_data["html"]
        assert cached["used_columns"] == preview_data["used_columns"]
        assert cached["filter_applicable"] == preview_data["filter_applicable"]


@pytest.mark.asyncio
async def test_cached_card_preview_different_filters(in_memory_cache):
    """異なるフィルタ値でのキャッシュテスト"""
    card_id = "card_test123"
    filters1 = {"category": "A"}
    filters2 = {"category": "B"}
    params = {}
    preview_data1 = {"html": "<div>Filter A</div>", "used_columns": [], "filter_applicable": []}
    preview_data2 = {"html": "<div>Filter B</div>", "used_columns": [], "filter_applicable": []}
    
    with patch('app.services.cache_service.get_cache_backend', return_value=in_memory_cache):
        # 異なるフィルタでキャッシュに保存
        await set_cached_card_preview(card_id, filters1, params, preview_data1, ttl_seconds=60)
        await set_cached_card_preview(card_id, filters2, params, preview_data2, ttl_seconds=60)
        
        # それぞれ正しく取得できる
        cached1 = await get_cached_card_preview(card_id, filters1, params)
        cached2 = await get_cached_card_preview(card_id, filters2, params)
        
        assert cached1["html"] == preview_data1["html"]
        assert cached2["html"] == preview_data2["html"]


@pytest.mark.asyncio
async def test_invalidate_card_preview_cache(in_memory_cache):
    """カードキャッシュの無効化テスト"""
    card_id = "card_test123"
    filters = {"category": "A"}
    params = {}
    preview_data = {"html": "<div>Test</div>", "used_columns": [], "filter_applicable": []}
    
    with patch('app.services.cache_service.get_cache_backend', return_value=in_memory_cache):
        # キャッシュに保存
        await set_cached_card_preview(card_id, filters, params, preview_data, ttl_seconds=60)
        
        # キャッシュから取得できることを確認
        cached = await get_cached_card_preview(card_id, filters, params)
        assert cached is not None
        
        # キャッシュを無効化
        await invalidate_card_preview_cache(card_id)
        
        # キャッシュから取得できないことを確認
        cached = await get_cached_card_preview(card_id, filters, params)
        assert cached is None
