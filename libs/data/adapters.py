from __future__ import annotations
from typing import List
from datetime import datetime
from libs.schemas.models import Candle, FundamentalsSnapshot, NewsItem
from libs.utils.config import settings
from libs.data.alpha_vantage import get_timeseries_alpha
from libs.data.news_api import get_news_newsapi
from libs.nlp.finbert import get_finbert
from libs.data.fmp import get_fundamentals_snapshot
from libs.utils.redis_cache import RedisCache

redis = RedisCache()

async def get_timeseries(symbol: str, start: datetime, end: datetime, interval: str = "1d") -> List[Candle]:
    if interval != "1d":
        raise NotImplementedError("Daily only in this example")
    
    cache_key = RedisCache.make_key("ts", {"symbol": symbol, "start": start.isoformat(), "end": end.isoformat(), "interval": interval})
    cached = await redis.get(cache_key)
    if cached:
        # reconstruct candles
        return [Candle(**c) for c in cached["candles"]]
    
    candles = await get_timeseries_alpha(symbol, start, end)
    await redis.set(cache_key, {"candles": [c.dict() for c in candles]})
    return candles

async def get_fundamentals(symbol: str, as_of: datetime) -> FundamentalsSnapshot:
    if not settings.fmp_api_key:
        # fallback minimal snapshot
        return FundamentalsSnapshot(symbol=symbol, as_of=as_of, pe=None, roe=None, debt_to_equity=None)
    
    cache_key = RedisCache.make_key("fund", {"symbol": symbol})
    cached = await redis.get(cache_key)
    if cached:
        return FundamentalsSnapshot(**cached)
    
    snap = await get_fundamentals_snapshot(symbol)
    fundamentals = FundamentalsSnapshot(
        symbol=symbol,
        as_of=snap["as_of"],
        pe=snap["pe"],
        roe=snap["roe"],
        debt_to_equity=snap["debt_to_equity"],
        profit_margin=snap["profit_margin"],
        growth_rev_yoy=snap["growth_rev_yoy"],
        source="fmp",
        filing_recency_days=snap["filing_recency_days"]
    )
    await redis.set(cache_key, fundamentals.dict())
    return fundamentals

async def get_news(symbol: str, start: datetime, end: datetime) -> list[NewsItem]:
    if not settings.news_api_key:
        return []
    
    cache_key = RedisCache.make_key("news", {"symbol": symbol, "start": start.isoformat(), "end": end.isoformat()})
    cached = await redis.get(cache_key)
    if cached:
        return [NewsItem(**n) for n in cached["items"]]
    
    items = await get_news_newsapi(symbol, start, end)
    finbert = get_finbert()
    items = finbert.score_articles(items)
    await redis.set(cache_key, {"items": [i.dict() for i in items]})
    return items