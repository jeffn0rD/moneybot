from libs.schemas.models import SentimentFeatures, AgentResult

def sentiment_agent(sent: SentimentFeatures) -> AgentResult:
    score = sent.weighted_sentiment or 0.0  # already -1..1 in our placeholder
    reasons = [f"avg_sent={sent.avg_sentiment}", f"volume={sent.news_volume}"]
    signal = "buy" if score > 0.1 else "sell" if score < -0.1 else "hold"
    conf = min(1.0, abs(score))
    return AgentResult(
        symbol=sent.symbol,
        as_of=sent.as_of,
        signal=signal,
        score=max(-1.0, min(1.0, score)),
        confidence=conf,
        rationale="; ".join(reasons),
        features_used={"weighted_sentiment": score},
        agent_version="sent_v1"
    )