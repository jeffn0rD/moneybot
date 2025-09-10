import json
import aioredis
import asyncio
import hashlib
from typing import Any, Optional
from libs.utils.config import settings

class RedisCache:
    def __init__(self, ttl: int = 300):
        self.ttl = ttl
        self._pool = None

    async def _conn(self):
        if self._pool is None:
            redis_url = getattr(settings, "redis_url", "redis://localhost:6379/0")
            self._pool = await aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        return self._pool

    @staticmethod
    def make_key(prefix: str, payload: dict) -> str:
        h = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
        return f"{prefix}:{h}"

    async def get(self, key: str) -> Optional[dict]:
        conn = await self._conn()
        out = await conn.get(key)
        return json.loads(out) if out else None

    async def set(self, key: str, value: dict):
        conn = await self._conn()
        await conn.set(key, json.dumps(value), ex=self.ttl)