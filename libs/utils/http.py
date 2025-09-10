from __future__ import annotations
import asyncio
from typing import Any, Dict, Optional
import httpx
import random

class HttpError(Exception):
    pass

async def get_json(
    url: str,
    params: Optional[Dict[str, Any]] = None,
    headers: Optional[Dict[str, str]] = None,
    timeout: float = 30.0,
    max_retries: int = 3,
    backoff_base: float = 0.5,
    backoff_jitter: float = 0.2,
) -> Any:
    attempt = 0
    last_exc: Exception | None = None
    async with httpx.AsyncClient(timeout=timeout) as client:
        while attempt <= max_retries:
            try:
                resp = await client.get(url, params=params, headers=headers)
                if resp.status_code == 429:
                    # Too many requests: exponential backoff
                    wait = backoff_base * (2 ** attempt) + random.uniform(0, backoff_jitter)
                    await asyncio.sleep(wait)
                    attempt += 1
                    continue
                resp.raise_for_status()
                return resp.json()
            except Exception as e:
                last_exc = e
                wait = backoff_base * (2 ** attempt) + random.uniform(0, backoff_jitter)
                await asyncio.sleep(wait)
                attempt += 1
        raise HttpError(f"Failed GET {url}: {last_exc}")