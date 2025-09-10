from datetime import datetime
from libs.schemas.models import ForecastResult, ModelFeatures
from libs.utils.config import settings
import random
import httpx

async def _remote_predict(symbol: str, as_of: datetime, features: dict, horizon: int):
    async with httpx.AsyncClient(timeout=15) as client:
        r = await client.post(
            settings.price_model_url,
            json={"symbol": symbol, "as_of": as_of.isoformat(), "features": features, "horizon_days": horizon}
        )
        r.raise_for_status()
        return r.json()

def price_model_agent(feats: ModelFeatures, horizon_days: int = 5) -> ForecastResult:
    # Keep sync for now; if use_remote_price_model is True, call async runner from orchestrator
    if settings.use_remote_price_model:
        raise RuntimeError("Remote price model requires async call usage in orchestrator")
    seed = int(feats.features_hash, 16) % (2**32 - 1)
    rnd = random.Random(seed)
    p50 = rnd.uniform(-0.02, 0.02)
    spread = rnd.uniform(0.01, 0.05)
    p10 = p50 - spread
    p90 = p50 + spread
    direction = "up" if p50 > 0.002 else "down" if p50 < -0.002 else "flat"
    conf = min(1.0, max(0.1, 1 - (p90 - p10)))
    return ForecastResult(
        symbol=feats.symbol,
        as_of=feats.as_of,
        horizon_days=horizon_days,
        p10=p10,
        p50=p50,
        p90=p90,
        exp_return=p50,
        direction=direction,
        confidence=conf,
        model_version="pm_stub_v1"
    )