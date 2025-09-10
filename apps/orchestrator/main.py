import sys
import os
from pathlib import Path

# Add the project root to Python path for cross-platform compatibility
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


import asyncio
from datetime import datetime, timedelta, timezone
from fastapi import FastAPI
from typing import Dict
from libs.utils.logging import setup_logger, ContextAdapter
from libs.utils.cache import InMemoryTTLCache
from libs.utils.config import settings
from libs.data.adapters import get_timeseries, get_fundamentals, get_news
from libs.features.engineering import (
    build_technical, build_fundamental, build_sentiment, build_model_features
)
from apps.agents.technical import technical_agent
from apps.agents.fundamental import fundamental_agent
from apps.agents.sentiment import sentiment_agent
from apps.agents.price_model import price_model_agent
from libs.schemas.models import EnsembleInput, ForecastResult
from libs.ensemble.meta import meta_ensemble
import httpx

logger = ContextAdapter(setup_logger("orchestrator"), {"trace_id": "-"})
cache = InMemoryTTLCache(ttl_seconds=settings.cache_ttl_s)
app = FastAPI(title="Multi-Agent Orchestrator")

async def _remote_price_predict(symbol: str, as_of, features: dict, horizon: int):
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.post(
            settings.price_model_url,
            json={"symbol": symbol, "as_of": as_of.isoformat(), "features": features, "horizon_days": horizon}
        )
        r.raise_for_status()
        return r.json()

async def analyze_symbol(symbol: str, horizon_days: int = 5, as_of: datetime | None = None) -> Dict:
    trace = f"{symbol}-{datetime.utcnow().timestamp()}"
    log = ContextAdapter(logger.logger, {"trace_id": trace})
    as_of = as_of or datetime.now(timezone.utc)
    start = as_of - timedelta(days=400)
    end = as_of

    cache_key = f"analysis:{symbol}:{horizon_days}"
    cached = cache.get(cache_key)
    if cached:
        log.info("cache hit", extra={"trace_id": trace})
        return cached

    log.info("begin analysis", extra={"trace_id": trace})

    # Create tasks for data fetching
    candles_task = asyncio.create_task(get_timeseries(symbol, start, end, "1d"))
    fund_task = asyncio.create_task(get_fundamentals(symbol, as_of))
    news_task = asyncio.create_task(get_news(symbol, as_of - timedelta(days=7), as_of))

    # Guardrails and error handling for provider calls
    try:
        candles, fund, news = await asyncio.gather(candles_task, fund_task, news_task)
    except Exception as e:
        log.info(f"provider error: {e}", extra={"trace_id": trace})
        # fallback: if news fails, proceed with empty; if prices fail, bubble up
        candles = await candles_task
        try:
            fund = await fund_task
        except Exception:
            from libs.schemas.models import FundamentalsSnapshot
            fund = FundamentalsSnapshot(symbol=symbol, as_of=as_of)
        try:
            news = await news_task
        except Exception:
            news = []

    tech = build_technical(candles)
    ffeat = build_fundamental(fund)
    sfeat = build_sentiment(news, as_of)
    mfeat = build_model_features(candles, tech, ffeat, sfeat)

    t_res = technical_agent(tech)
    f_res = fundamental_agent(ffeat)
    s_res = sentiment_agent(sfeat)
    
    # Use remote price model if configured, otherwise use local stub
    if settings.use_remote_price_model:
        pm = await _remote_price_predict(mfeat.symbol, mfeat.as_of, {"features_hash": mfeat.features_hash}, horizon_days)
        m_res = ForecastResult(
            symbol=mfeat.symbol,
            as_of=mfeat.as_of,
            horizon_days=horizon_days,
            p10=pm["p10"], p50=pm["p50"], p90=pm["p90"],
            exp_return=pm["exp_return"],
            direction=pm["direction"],
            confidence=pm["confidence"],
            model_version="external_stub_v1"
        )
    else:
        m_res = price_model_agent(mfeat, horizon_days=horizon_days)

    ensemble_in = EnsembleInput(technical=t_res, fundamental=f_res, sentiment=s_res, forecast=m_res)
    decision = meta_ensemble(ensemble_in)

    result = {
        "decision": decision.dict(),
        "agents": {
            "technical": t_res.dict(),
            "fundamental": f_res.dict(),
            "sentiment": s_res.dict(),
            "forecast": m_res.dict()
        }
    }
    cache.set(cache_key, result)
    log.info("end analysis", extra={"trace_id": trace})
    return result

@app.get("/analyze/{symbol}")
async def analyze(symbol: str, horizon_days: int = 5):
    return await analyze_symbol(symbol, horizon_days=horizon_days)