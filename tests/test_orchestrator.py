import pytest
import anyio
from apps.orchestrator.main import analyze_symbol

@pytest.mark.anyio
async def test_analyze_symbol_runs():
    res = await analyze_symbol("AAPL", horizon_days=5)
    assert "decision" in res
    assert "agents" in res
    assert res["decision"]["prob_up"] >= 0.0