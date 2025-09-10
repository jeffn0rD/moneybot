from __future__ import annotations
from libs.schemas.models import EnsembleInput, EnsembleDecision, Signal
from libs.utils.cache import hash_dict
from libs.utils.config import settings
from datetime import datetime
import os
import pickle
import math

_cached_model = None
_cached_spec = None

def _load_meta_if_available():
    global _cached_model, _cached_spec
    if _cached_model is not None:
        return _cached_model, _cached_spec
    path = settings.meta_model_path
    if os.path.exists(path):
        with open(path, "rb") as f:
            obj = pickle.load(f)
        _cached_model = obj["model"]
        _cached_spec = obj["spec"]
    return _cached_model, _cached_spec

def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-x))

def _simple_baseline(inp: EnsembleInput) -> tuple[float, float]:
    w_tech, w_fund, w_sent, w_fc = 0.3, 0.3, 0.2, 0.4
    x = (
        w_tech * inp.technical.score * inp.technical.confidence +
        w_fund * inp.fundamental.score * inp.fundamental.confidence +
        w_sent * inp.sentiment.score * inp.sentiment.confidence +
        w_fc * inp.forecast.exp_return * (2.0 * inp.forecast.confidence)
    )
    prob_up = _sigmoid(5.0 * x)
    uncertainty = max(0.0, 1.0 - abs(x))
    return prob_up, uncertainty

def meta_ensemble(inp: EnsembleInput) -> EnsembleDecision:
    model, spec = _load_meta_if_available()
    if model is not None:
        order = spec["feature_order"]
        feats = {
            "t_score": inp.technical.score, "t_conf": inp.technical.confidence,
            "f_score": inp.fundamental.score, "f_conf": inp.fundamental.confidence,
            "s_score": inp.sentiment.score, "s_conf": inp.sentiment.confidence,
            "m_exp": inp.forecast.exp_return, "m_conf": inp.forecast.confidence
        }
        X = [[feats[k] for k in order]]
        prob_up = float(model.predict_proba(X)[0, 1])
        # simple uncertainty proxy: entropy
        p = prob_up
        eps = 1e-6
        uncertainty = - (p*math.log(p+eps) + (1-p)*math.log(1-p+eps)) / math.log(2)
    else:
        prob_up, uncertainty = _simple_baseline(inp)

    signal: Signal = "buy" if prob_up > 0.55 else "sell" if prob_up < 0.45 else "hold"
    size = max(0.0, min(1.0, (prob_up - 0.5) * 2.0)) if signal != "hold" else 0.0

    versions = {
        "technical": inp.technical.agent_version,
        "fundamental": inp.fundamental.agent_version,
        "sentiment": inp.sentiment.agent_version,
        "forecast": inp.forecast.model_version,
        "ensemble": "meta_lgbm" if model is not None else "meta_stub_v1"
    }
    inputs_hash = hash_dict({
        "t": inp.technical.score, "tf": inp.technical.confidence,
        "f": inp.fundamental.score, "ff": inp.fundamental.confidence,
        "s": inp.sentiment.score, "sf": inp.sentiment.confidence,
        "m": inp.forecast.exp_return, "mc": inp.forecast.confidence
    })
    return EnsembleDecision(
        symbol=inp.technical.symbol,
        as_of=inp.technical.as_of,
        horizon_days=inp.forecast.horizon_days,
        prob_up=prob_up,
        uncertainty=uncertainty,
        signal=signal,
        size=size,
        rationale="Meta-learner ensemble" if model is not None else "Weighted blend baseline",
        versions=versions,
        inputs_hash=inputs_hash
    )