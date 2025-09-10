from datetime import datetime
from libs.schemas.models import TechnicalFeatures, AgentResult
from typing import Optional

def technical_agent(tech: TechnicalFeatures) -> AgentResult:
    # Simple scoring: combine RSI/MACD/BB signals
    score = 0.0
    rationale_parts = []
    if tech.rsi is not None:
        if tech.rsi < 30: score += 0.3; rationale_parts.append("RSI oversold")
        elif tech.rsi > 70: score -= 0.3; rationale_parts.append("RSI overbought")
    if tech.macd is not None and tech.macd_signal is not None:
        if tech.macd > tech.macd_signal: score += 0.3; rationale_parts.append("MACD bullish")
        else: score -= 0.1; rationale_parts.append("MACD bearish-ish")
    if tech.bb_lower and tech.bb_upper:
        # naive: if close below lower band or above upper band would need close.
        pass
    signal = "buy" if score > 0.15 else "sell" if score < -0.15 else "hold"
    conf = min(1.0, abs(score))
    return AgentResult(
        symbol=tech.symbol,
        as_of=tech.as_of,
        signal=signal,
        score=max(-1.0, min(1.0, score)),
        confidence=conf,
        rationale="; ".join(rationale_parts),
        features_used={"rsi": tech.rsi or 50.0, "macd": tech.macd or 0.0},
        agent_version="tech_v1"
    )