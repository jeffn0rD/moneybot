from datetime import datetime, timezone
from libs.schemas.models import AgentResult

def test_agent_result_bounds():
    ar = AgentResult(symbol="AAPL", as_of=datetime.now(timezone.utc), signal="hold", score=0.0, confidence=0.5)
    assert ar.score == 0.0
    assert 0.0 <= ar.confidence <= 1.0