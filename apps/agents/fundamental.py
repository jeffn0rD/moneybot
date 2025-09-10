from libs.schemas.models import FundamentalFeatures, AgentResult

def fundamental_agent(fund: FundamentalFeatures) -> AgentResult:
    score = 0.0
    reasons = []
    if fund.pe is not None:
        if fund.pe < 18: score += 0.2; reasons.append("PE reasonable")
        elif fund.pe > 35: score -= 0.2; reasons.append("PE rich")
    if fund.roe is not None:
        if fund.roe > 0.15: score += 0.3; reasons.append("High ROE")
        elif fund.roe < 0.05: score -= 0.2; reasons.append("Low ROE")
    if fund.d2e is not None:
        if fund.d2e < 0.8: score += 0.1; reasons.append("Manageable leverage")
        elif fund.d2e > 2.0: score -= 0.2; reasons.append("High leverage")

    signal = "buy" if score > 0.15 else "sell" if score < -0.15 else "hold"
    conf = min(1.0, abs(score))
    return AgentResult(
        symbol=fund.symbol,
        as_of=fund.as_of,
        signal=signal,
        score=max(-1.0, min(1.0, score)),
        confidence=conf,
        rationale="; ".join(reasons),
        features_used={"pe": fund.pe or 0.0, "roe": fund.roe or 0.0, "d2e": fund.d2e or 0.0},
        agent_version="fund_v1"
    )