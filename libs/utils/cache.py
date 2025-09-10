import time
import hashlib
from typing import Any, Dict, Tuple

class InMemoryTTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl = ttl_seconds
        self.store: Dict[str, Tuple[float, Any]] = {}

    def _now(self) -> float:
        return time.time()

    def _expired(self, ts: float) -> bool:
        return (self._now() - ts) > self.ttl

    def get(self, key: str):
        item = self.store.get(key)
        if not item:
            return None
        ts, value = item
        if self._expired(ts):
            self.store.pop(key, None)
            return None
        return value

    def set(self, key: str, value: Any):
        self.store[key] = (self._now(), value)

def hash_dict(d: Dict) -> str:
    m = hashlib.sha256()
    m.update(repr(sorted(d.items())).encode())
    return m.hexdigest()