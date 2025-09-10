from __future__ import annotations
from typing import List, Optional, Dict, Literal, Tuple
from pydantic import BaseModel, Field, validator
from datetime import datetime


Signal = Literal["buy", "hold", "sell"]

class Candle(BaseModel):
    symbol: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    interval: Literal["1min", "5min", "15min", "1h", "1d"] = "1d"
    source: str = "alpha_vantage"

class FundamentalsSnapshot(BaseModel):
    symbol: str
    as_of: datetime
    pe: Optional[float] = None
    roe: Optional[float] = None
    debt_to_equity: Optional[float] = None
    revenue_ttm: Optional[float] = None
    eps_ttm: Optional[float] = None
    profit_margin: Optional[float] = None
    growth_rev_yoy: Optional[float] = None
    source: str = "fmp"
    filing_recency_days: Optional[int] = None

class NewsItem(BaseModel):
    symbol: str
    published_at: datetime
    title: str
    summary: Optional[str] = None
    source: Optional[str] = None
    url: Optional[str] = None
    # Optional model inferences
    sentiment_score: Optional[float] = None  # -1..1
    sentiment_confidence: Optional[float] = None  # 0..1
    topic: Optional[str] = None

class TechnicalFeatures(BaseModel):
    symbol: str
    as_of: datetime
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    bb_upper: Optional[float] = None
    bb_lower: Optional[float] = None
    atr: Optional[float] = None
    sma_20: Optional[float] = None
    ema_50: Optional[float] = None
    feature_version: str = "tech_v1"

class FundamentalFeatures(BaseModel):
    symbol: str
    as_of: datetime
    pe: Optional[float] = None
    roe: Optional[float] = None
    d2e: Optional[float] = None
    profit_margin: Optional[float] = None
    growth_rev_yoy: Optional[float] = None
    feature_version: str = "fund_v1"

class SentimentFeatures(BaseModel):
    symbol: str
    as_of: datetime
    avg_sentiment: Optional[float] = None  # -1..1
    news_volume: int = 0
    weighted_sentiment: Optional[float] = None
    feature_version: str = "sent_v1"

class ModelFeatures(BaseModel):
    symbol: str
    as_of: datetime
    # Placeholder for model-ready tensors/features (store hashes, not raw arrays)
    features_hash: str
    feature_version: str = "model_v1"

class AgentResult(BaseModel):
    symbol: str
    as_of: datetime
    signal: Signal
    score: float = Field(..., ge=-1.0, le=1.0)   # -1..1
    confidence: float = Field(..., ge=0.0, le=1.0)
    rationale: Optional[str] = None
    inputs_hash: Optional[str] = None
    time_window: Optional[str] = None
    features_used: Optional[Dict[str, float]] = None
    agent_version: str = "v1"

class ForecastResult(BaseModel):
    symbol: str
    as_of: datetime
    horizon_days: int
    p10: float
    p50: float
    p90: float
    exp_return: float
    direction: Literal["up", "down", "flat"]
    confidence: float = Field(..., ge=0.0, le=1.0)
    model_version: str = "pm_v1"

class EnsembleInput(BaseModel):
    technical: AgentResult
    fundamental: AgentResult
    sentiment: AgentResult
    forecast: ForecastResult

class EnsembleDecision(BaseModel):
    symbol: str
    as_of: datetime
    horizon_days: int
    prob_up: float = Field(..., ge=0.0, le=1.0)
    uncertainty: float = Field(..., ge=0.0, le=1.0)
    signal: Signal
    size: float = Field(..., ge=0.0, le=1.0)  # position fraction
    rationale: Optional[str] = None
    versions: Dict[str, str] = {}
    inputs_hash: Optional[str] = None