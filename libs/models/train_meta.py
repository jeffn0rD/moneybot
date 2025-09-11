from __future__ import annotations
import sys
import os
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import pickle

# jpr 091025
import argparse

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score
from lightgbm import LGBMClassifier

from libs.data.adapters import get_timeseries, get_fundamentals, get_news
from libs.features.engineering import build_technical, build_fundamental, build_sentiment, build_model_features
from apps.agents.technical import technical_agent
from apps.agents.fundamental import fundamental_agent
from apps.agents.sentiment import sentiment_agent
from apps.agents.price_model import price_model_agent
from libs.schemas.models import EnsembleInput
from libs.utils.config import settings

def compute_forward_return(candles: List, as_of_idx: int, horizon_days: int) -> float:
    # candles must be daily sorted ascending. Use close->close return horizon_days ahead.
    if as_of_idx + horizon_days >= len(candles):
        return np.nan
    p0 = candles[as_of_idx].close
    p1 = candles[as_of_idx + horizon_days].close
    return (p1 - p0) / p0

def to_feature_row(symbol: str, as_of_idx: int, candles: List, horizon_days: int, as_of: datetime):
    # Build all features and agent outputs at time index
    sub_candles = candles[:as_of_idx+1]
    tech = build_technical(sub_candles)
    fund = await_or_sync(get_fundamentals(symbol, as_of))
    sent_news = await_or_sync(get_news(symbol, as_of - timedelta(days=7), as_of))
    sent = build_sentiment(sent_news, as_of)
    mfeat = build_model_features(sub_candles, tech, build_fundamental(fund), sent)

    t_res = technical_agent(tech)
    f_res = fundamental_agent(build_fundamental(fund))
    s_res = sentiment_agent(sent)
    m_res = price_model_agent(mfeat, horizon_days=horizon_days)

    # Meta features
    feats = {
        "t_score": t_res.score, "t_conf": t_res.confidence,
        "f_score": f_res.score, "f_conf": f_res.confidence,
        "s_score": s_res.score, "s_conf": s_res.confidence,
        "m_exp": m_res.exp_return, "m_conf": m_res.confidence
    }
    return feats

def await_or_sync(coro):
    # Helper to run async calls in sync training script
    import asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_running():
        # In notebooks, we may need nest_asyncio; here we'll create a new loop
        new_loop = asyncio.new_event_loop()
        out = new_loop.run_until_complete(coro)
        new_loop.close()
        return out
    else:
        return loop.run_until_complete(coro)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, required=True)
    parser.add_argument("--start", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--end", type=str, required=True, help="YYYY-MM-DD")
    parser.add_argument("--horizon", type=int, default=5)
    parser.add_argument("--outfile", type=str, default="models/meta_lgbm.pkl")
    args = parser.parse_args()

    os.makedirs("models", exist_ok=True)

    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)
    symbol = args.symbol
    horizon = args.horizon

    candles = await_or_sync(get_timeseries(symbol, start - timedelta(days=60), end + timedelta(days=1)))
    if len(candles) < 100:
        raise ValueError("Not enough candles")

    X_rows = []
    y = []
    dates = []
    # Use every 5 trading days as an observation
    for i in range(40, len(candles) - horizon, 5):
        as_of = candles[i].ts
        feats = to_feature_row(symbol, i, candles, horizon, as_of)
        fwd = compute_forward_return(candles, i, horizon)
        if np.isnan(fwd):
            continue
        X_rows.append(list(feats.values()))
        y.append(1 if fwd > 0 else 0)
        dates.append(as_of)

    X = np.array(X_rows)
    y = np.array(y)
    if len(y) < 50:
        raise ValueError("Not enough training samples")

    # Train/valid split (time-based)
    split = int(len(y) * 0.8)
    Xtr, Xva = X[:split], X[split:]
    ytr, yva = y[:split], y[split:]

    clf = LGBMClassifier(
        n_estimators=400,
        learning_rate=0.05,
        max_depth=-1,
        num_leaves=31,
        subsample=0.9,
        colsample_bytree=0.8,
        random_state=42
    )
    clf.fit(Xtr, ytr)
    pva = clf.predict_proba(Xva)[:, 1]
    auc = roc_auc_score(yva, pva)
    print(f"Validation AUC: {auc:.3f}")

    meta_spec = {
        "feature_order": ["t_score", "t_conf", "f_score", "f_conf", "s_score", "s_conf", "m_exp", "m_conf"],
        "horizon": horizon,
        "symbol": symbol,
        "auc": float(auc)
    }
    with open(args.outfile, "wb") as f:
        pickle.dump({"model": clf, "spec": meta_spec}, f)
    print(f"Saved model to {args.outfile}")

if __name__ == "__main__":
    main()