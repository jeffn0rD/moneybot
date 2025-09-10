import sys
import os
from pathlib import Path

# Add the project root to Python path for cross-platform compatibility
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))


from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import List, Dict
import math
import asyncio
import argparse

from libs.schemas.models import Candle
from libs.data.adapters import get_timeseries
from apps.orchestrator.main import analyze_symbol

async def walk_forward_backtest(symbol: str, start: datetime, end: datetime, horizon_days: int = 5) -> Dict:
    cursor = start
    equity = 1.0
    equity_curve = []
    while cursor + timedelta(days=horizon_days + 7) < end:
        res = await analyze_symbol(symbol, horizon_days=horizon_days, as_of=cursor)
        dec = res["decision"]
        signal = dec["signal"]
        size = dec["size"]
        candles = await get_timeseries(symbol, cursor, cursor + timedelta(days=horizon_days + 1))
        if len(candles) < 2:
            cursor += timedelta(days=7)
            continue
        entry = candles[1].open
        exitp = candles[-1].close
        ret = (exitp - entry) / entry
        if signal == "buy":
            equity *= (1.0 + size * ret)
        elif signal == "sell":
            equity *= (1.0 - size * ret)
        equity_curve.append((cursor, equity))
        cursor += timedelta(days=7)
    return {"final_equity": equity, "equity_curve": equity_curve}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbol", type=str, default="AAPL")
    parser.add_argument("--start", type=str, default="2022-01-01")
    parser.add_argument("--end", type=str, default="2024-12-31")
    parser.add_argument("--horizon", type=int, default=5)
    args = parser.parse_args()
    start = datetime.fromisoformat(args.start).replace(tzinfo=timezone.utc)
    end = datetime.fromisoformat(args.end).replace(tzinfo=timezone.utc)

    res = asyncio.run(walk_forward_backtest(args.symbol, start, end, args.horizon))
    print(f"Final equity: {res['final_equity']:.3f}")
    print(f"Points: {len(res['equity_curve'])}")

if __name__ == "__main__":
    main()