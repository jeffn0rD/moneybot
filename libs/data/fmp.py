from __future__ import annotations
from datetime import datetime, timezone
from typing import Optional, Dict, Any
from libs.utils.config import settings
from libs.utils.http import get_json
from libs.utils.limits import fmp_semaphore

# Docs: https://site.financialmodelingprep.com/developer/docs

def _with_key(params: dict[str, Any]) -> dict[str, Any]:
    p = dict(params)
    p["apikey"] = settings.fmp_api_key
    return p

async def _get(url: str, params: dict[str, Any]):
    async with fmp_semaphore:
        return await get_json(url, params=params)

async def get_company_profile(symbol: str) -> Optional[dict]:
    url = f"{settings.fmp_base}/profile/{symbol}"
    data = await _get(url, _with_key({}))
    if isinstance(data, list) and data:
        return data[0]
    return None

async def get_key_metrics(symbol: str) -> Optional[dict]:
    # Returns list over years; use most recent
    url = f"{settings.fmp_base}/key-metrics/{symbol}"
    data = await _get(url, _with_key({"limit": 1}))
    if isinstance(data, list) and data:
        return data[0]
    return None

async def get_income_statement(symbol: str) -> Optional[dict]:
    url = f"{settings.fmp_base}/income-statement/{symbol}"
    data = await _get(url, _with_key({"limit": 1}))
    if isinstance(data, list) and data:
        return data[0]
    return None

async def get_balance_sheet(symbol: str) -> Optional[dict]:
    url = f"{settings.fmp_base}/balance-sheet-statement/{symbol}"
    data = await _get(url, _with_key({"limit": 1}))
    if isinstance(data, list) and data:
        return data[0]
    return None

def _parse_date(s: str | None) -> datetime | None:
    if not s:
        return None
    try:
        # FMP returns '2024-12-31', no timezone
        return datetime.fromisoformat(s).replace(tzinfo=timezone.utc)
    except Exception:
        return None

async def get_fundamentals_snapshot(symbol: str) -> dict:
    profile = await get_company_profile(symbol) or {}
    metrics = await get_key_metrics(symbol) or {}
    income = await get_income_statement(symbol) or {}
    balance = await get_balance_sheet(symbol) or {}

    # Recency: prefer incomeStatement date
    as_of = _parse_date(income.get("date")) or _parse_date(profile.get("ipoDate")) or datetime.now(timezone.utc)
    recency_days = int((datetime.now(timezone.utc) - as_of).days) if as_of else None

    # PE from profile or metrics
    pe = profile.get("pe") or metrics.get("peRatio") or None
    roe = metrics.get("returnOnEquityTTM") or metrics.get("roe") or None
    d2e = metrics.get("debtToEquity") or None

    margin = (income.get("netIncome") / income.get("revenue")) if income.get("revenue") else None
    growth_rev_yoy = metrics.get("revenueGrowth") if metrics.get("revenueGrowth") is not None else None

    return {
        "symbol": symbol,
        "as_of": as_of,
        "pe": float(pe) if pe is not None else None,
        "roe": float(roe) if roe is not None else None,
        "debt_to_equity": float(d2e) if d2e is not None else None,
        "profit_margin": float(margin) if margin is not None else None,
        "growth_rev_yoy": float(growth_rev_yoy) if growth_rev_yoy is not None else None,
        "filing_recency_days": recency_days
    }