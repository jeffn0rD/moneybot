from __future__ import annotations
from typing import List
from datetime import datetime
import pandas as pd
from libs.schemas.models import Candle
from libs.utils.config import settings
from libs.utils.http import get_json
from libs.utils.limits import alpha_semaphore

async def fetch_alpha_vantage(symbol: str) -> pd.DataFrame:
    params = {
        "function": "TIME_SERIES_DAILY_ADJUSTED",
        "symbol": symbol,
        "apikey": settings.alpha_vantage_key,
        "outputsize": "full"
    }
    async with alpha_semaphore:
        data = await get_json(settings.alphavantage_base, params=params)
    key = "Time Series (Daily)"
    if key not in data:
        raise ValueError(f"Alpha Vantage error or limit: {data}")
    df = pd.DataFrame.from_dict(data[key], orient="index")
    df.index = pd.to_datetime(df.index, utc=True)
    df = df.sort_index()
    df = df.rename(columns={
        "1. open": "open",
        "2. high": "high",
        "3. low": "low",
        "4. close": "close",
        "6. volume": "volume"
    })[["open", "high", "low", "close", "volume"]].astype(float)
    return df

async def get_timeseries_alpha(symbol: str, start: datetime, end: datetime) -> List[Candle]:
    df = await fetch_alpha_vantage(symbol)
    df = df.loc[(df.index >= pd.Timestamp(start, tz="UTC")) & (df.index <= pd.Timestamp(end, tz="UTC"))]
    candles: List[Candle] = []
    for ts, row in df.iterrows():
        candles.append(Candle(
            symbol=symbol,
            ts=ts.to_pydatetime(),
            open=float(row["open"]),
            high=float(row["high"]),
            low=float(row["low"]),
            close=float(row["close"]),
            volume=float(row["volume"]),
            interval="1d",
            source="alpha_vantage"
        ))
    return candles