"""キャッシュサービス"""
import json
import hashlib
from typing import Optional, Any
from datetime import datetime, timedelta

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class CacheBackend:
    """キャッシュバックエンドのインターフェース"""
    
    async def get(self, key: str) -> Optional[str]:
        """キャッシュから値を取得"""
        raise NotImplementedError
    
    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """キャッシュに値を設定"""
        raise NotImplementedError
    
    async def delete(self, key: str) -> None:
        """キャッシュから値を削除"""
        raise NotImplementedError


class InMemoryCacheBackend(CacheBackend):
    """インメモリキャッシュバックエンド（開発環境用）"""
    
    def __init__(self):
        self._cache: dict[str, tuple[str, datetime]] = {}
    
    async def get(self, key: str) -> Optional[str]:
        """キャッシュから値を取得"""
        if key not in self._cache:
            return None
        
        value, expiry = self._cache[key]
        
        # TTLチェック
        if datetime.utcnow() > expiry:
            del self._cache[key]
            return None
        
        return value
    
    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """キャッシュに値を設定"""
        expiry = datetime.utcnow() + timedelta(seconds=ttl_seconds)
        self._cache[key] = (value, expiry)
    
    async def delete(self, key: str) -> None:
        """キャッシュから値を削除"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self) -> None:
        """キャッシュをクリア（テスト用）"""
        self._cache.clear()


class RedisCacheBackend(CacheBackend):
    """Redisキャッシュバックエンド（本番環境用）"""
    
    def __init__(self, redis_url: str):
        self._redis_url = redis_url
        self._redis_client: Optional[Any] = None
    
    async def _get_client(self):
        """Redisクライアントを取得（遅延初期化）"""
        if self._redis_client is None:
            try:
                import redis.asyncio as redis
                self._redis_client = redis.from_url(self._redis_url)
            except ImportError:
                logger.error("redis package not installed. Install with: pip install redis")
                raise
        return self._redis_client
    
    async def get(self, key: str) -> Optional[str]:
        """キャッシュから値を取得"""
        try:
            client = await self._get_client()
            value = await client.get(key)
            return value.decode('utf-8') if value else None
        except Exception as e:
            logger.error(f"Redis get error: {e}", exc_info=True)
            return None
    
    async def set(self, key: str, value: str, ttl_seconds: int) -> None:
        """キャッシュに値を設定"""
        try:
            client = await self._get_client()
            await client.setex(key, ttl_seconds, value)
        except Exception as e:
            logger.error(f"Redis set error: {e}", exc_info=True)
            # エラー時は続行（キャッシュ失敗は致命的ではない）
    
    async def delete(self, key: str) -> None:
        """キャッシュから値を削除"""
        try:
            client = await self._get_client()
            await client.delete(key)
        except Exception as e:
            logger.error(f"Redis delete error: {e}", exc_info=True)


# グローバルキャッシュバックエンドインスタンス
_cache_backend: Optional[CacheBackend] = None


def get_cache_backend() -> CacheBackend:
    """キャッシュバックエンドを取得（シングルトン）"""
    global _cache_backend
    
    if _cache_backend is None:
        redis_url = getattr(settings, 'redis_url', None)
        
        if redis_url:
            _cache_backend = RedisCacheBackend(redis_url)
            logger.info("Using Redis cache backend")
        else:
            _cache_backend = InMemoryCacheBackend()
            logger.info("Using in-memory cache backend (development)")
    
    return _cache_backend


def generate_cache_key(card_id: str, filters: dict[str, Any], params: dict[str, Any]) -> str:
    """キャッシュキーを生成"""
    filters_str = json.dumps(filters, sort_keys=True)
    params_str = json.dumps(params, sort_keys=True)
    combined_str = f"{filters_str}|{params_str}"
    combined_hash = hashlib.sha256(combined_str.encode()).hexdigest()[:16]
    return f"card_preview:{card_id}:{combined_hash}"


async def get_cached_card_preview(
    card_id: str,
    filters: dict[str, Any],
    params: dict[str, Any],
) -> Optional[dict[str, Any]]:
    """キャッシュからカードプレビューを取得"""
    cache = get_cache_backend()
    key = generate_cache_key(card_id, filters, params)
    
    cached_value = await cache.get(key)
    if cached_value is None:
        return None
    
    try:
        return json.loads(cached_value)
    except json.JSONDecodeError:
        logger.warning(f"Failed to decode cached value for key: {key}")
        await cache.delete(key)
        return None


async def set_cached_card_preview(
    card_id: str,
    filters: dict[str, Any],
    params: dict[str, Any],
    preview_data: dict[str, Any],
    ttl_seconds: int = 3600,
) -> None:
    """カードプレビューをキャッシュに保存"""
    cache = get_cache_backend()
    key = generate_cache_key(card_id, filters, params)
    
    try:
        value = json.dumps(preview_data)
        await cache.set(key, value, ttl_seconds)
    except Exception as e:
        logger.error(f"Failed to cache card preview: {e}", exc_info=True)
        # キャッシュ失敗は致命的ではないので続行


async def invalidate_card_preview_cache(card_id: str) -> None:
    """カードのキャッシュを無効化（カード更新時など）"""
    cache = get_cache_backend()
    
    if isinstance(cache, InMemoryCacheBackend):
        prefix = f"card_preview:{card_id}:"
        keys_to_delete = [
            key for key in cache._cache.keys()
            if key.startswith(prefix)
        ]
        for key in keys_to_delete:
            await cache.delete(key)
    else:
        logger.info(
            f"Cache invalidation for card {card_id} skipped (Redis pattern delete not implemented)"
        )
