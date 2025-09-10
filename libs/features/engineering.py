from __future__ import annotations
from typing import List, Tuple
from dataclasses import dataclass
from datetime import datetime
import math
from libs.schemas.models import (
    Candle,
    FundamentalsSnapshot,
    NewsItem,
    TechnicalFeatures,
    FundamentalFeatures,
    SentimentFeatures,
    ModelFeatures,
)
from libs.utils.cache import hash_dict


def _simple_rsi(prices: List[float], period: int = 14) -> float:
    if len(prices) < period + 1:
        return float("nan")
    gains, losses = [], []
    for i in range(1, period + 1):
        diff = prices[-i] - prices[-i-1]
        gains.append(max(diff, 0))
        losses.append(abs(min(diff, 0)))
    avg_gain = sum(gains) / period
    avg_loss = sum(losses) / period
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def _simple_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9):
    # super simplified EMA approximations
    def ema(vals, p):
        k = 2 / (p + 1)
        e = vals[0]
        for v in vals[1:]:
            e = v * k + e * (1 - k)
        return e
    if len(prices) < slow + signal:
        return (float("nan"), float("nan"))
    macd_line = ema(prices[-slow:], fast) - ema(prices[-slow:], slow)
    signal_line = ema([macd_line] * signal, signal)
    return macd_line, signal_line

def build_technical(candles: List[Candle]) -> TechnicalFeatures:
    if not candles:
        raise ValueError("No candles provided")
    closes = [c.close for c in candles]
    as_of = candles[-1].ts
    rsi = _simple_rsi(closes)
    macd, macd_sig = _simple_macd(closes)
    bb_period = 20
    if len(closes) >= bb_period:
        m = sum(closes[-bb_period:]) / bb_period
        var = sum((x - m) ** 2 for x in closes[-bb_period:]) / bb_period
        sd = math.sqrt(var)
        bb_upper = m + 2 * sd
        bb_lower = m - 2 * sd
    else:
        bb_upper, bb_lower = float("nan"), float("nan")

    return TechnicalFeatures(
        symbol=candles[-1].symbol,
        as_of=as_of,
        rsi=rsi,
        macd=macd,
        macd_signal=macd_sig,
        bb_upper=bb_upper,
        bb_lower=bb_lower,
        atr=None,
        sma_20=None,
        ema_50=None,
    )

def build_fundamental(snapshot: FundamentalsSnapshot) -> FundamentalFeatures:
    return FundamentalFeatures(
        symbol=snapshot.symbol,
        as_of=snapshot.as_of,
        pe=snapshot.pe,
        roe=snapshot.roe,
        d2e=snapshot.debt_to_equity,
        profit_margin=snapshot.profit_margin,
        growth_rev_yoy=snapshot.growth_rev_yoy,
    )

def build_sentiment(news: List[NewsItem], as_of: datetime) -> SentimentFeatures:
    # Time-decay weighting: newer news weighs more. Source-neutral for now.
    if not news:
        return SentimentFeatures(symbol="", as_of=as_of, avg_sentiment=0.0, news_volume=0, weighted_sentiment=0.0)
    sym = news[0].symbol
    weights, scores = [], []
    for n in news:
        # Default to 0 if not set
        s = n.sentiment_score if n.sentiment_score is not None else 0.0
        # Decay by age (half-life 3 days)
        age_days = max(0.0, (as_of - n.published_at.replace(tzinfo=timezone.utc)).total_seconds() / 86400.0) if n.published_at.tzinfo else (as_of - n.published_at).total_seconds()/86400.0
        w = 0.5 ** (age_days / 3.0)
        weights.append(w)
        scores.append(s)
    if sum(weights) == 0:
        avg = 0.0
        wavg = 0.0
    else:
        avg = sum(scores) / len(scores)
        wavg = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
    return SentimentFeatures(symbol=sym, as_of=as_of, avg_sentiment=avg, news_volume=len(news), weighted_sentiment=wavg)

@dataclass
class ModelPrep:
    features: dict
    features_hash: str

def build_model_features(candles: List[Candle], tech: TechnicalFeatures, fund: FundamentalFeatures, sent: SentimentFeatures) -> ModelFeatures:
    # Minimal model features: latest close return proxy and a few engineered fields
    feat = {
        "rsi": tech.rsi or 50.0,
        "macd": tech.macd or 0.0,
        "pe": fund.pe or 20.0,
        "roe": fund.roe or 0.1,
        "sent": sent.weighted_sentiment or 0.0,
    }
    features_hash = hash_dict(feat)
    return ModelFeatures(symbol=candles[-1].symbol, as_of=candles[-1].ts, features_hash=features_hash)