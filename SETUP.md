# MoneyBot Local Development Setup Guide

## Quick Start

### 1. Environment Setup
```bash
# Clone and navigate to the project
cd moneybot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Variables
```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys:
# ALPHA_VANTAGE_KEY=your_key_here
# NEWS_API_KEY=your_key_here
# FMP_API_KEY=your_key_here
```

### 3. Run the System

#### Option A: Direct Python (Development)
```bash
# Start the orchestrator
uvicorn apps.orchestrator.main:app --reload --host 0.0.0.0 --port 8000
```

#### Option B: Docker (Production-like)
```bash
# Build and start all services
docker-compose up --build

# The orchestrator will be available at http://localhost:8000
```

### 4. Test the API

#### Basic Health Check
```bash
curl http://localhost:8000/analyze/AAPL?horizon_days=5
```

#### Expected Response Structure
```json
{
  "decision": {
    "symbol": "AAPL",
    "as_of": "2024-01-01T00:00:00Z",
    "signal": "buy",
    "prob_up": 0.62,
    "uncertainty": 0.15,
    "size": 0.24
  },
  "agents": {
    "technical": {...},
    "fundamental": {...},
    "sentiment": {...},
    "forecast": {...}
  }
}
```

### 5. Run Tests
```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest tests/test_schemas.py -v
pytest tests/test_orchestrator.py -v
```

### 6. Development Workflow

#### Adding a New Agent
1. Create `apps/agents/your_agent.py`
2. Follow the pattern of existing agents
3. Update the orchestrator in `main.py`
4. Add tests in `tests/`

#### Replacing Stub Adapters
1. Modify `libs/data/adapters.py` with real API calls
2. Add retry logic and caching
3. Update error handling

#### Enhancing Features
1. Update feature engineering in `libs/features/engineering.py`
2. Add new technical indicators in `build_technical()`
3. Add new fundamental metrics in `build_fundamental()`

### 7. Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Feature Engine  │───▶│     Agents      │
│                 │    │                  │    │                 │
│ • Alpha Vantage │    • Technical       │    • Technical      │
│ • News API      │    • Fundamental     │    • Fundamental    │
│ • FMP API       │    • Sentiment       │    • Sentiment      │
└─────────────────┘    • Model Features  │    • Price Model    │
                       └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Meta Ensemble  │
                                                │                 │
                                                │  Final Decision │
                                                └─────────────────┘
```

### 8. Performance Tips

- **Caching**: Results are cached for 5 minutes by default
- **Async**: All data fetching is async for better performance
- **Error Handling**: Each agent has graceful fallbacks

### 9. Next Steps

1. **Replace stubs**: Update data adapters with real API calls
2. **Add ML models**: Replace price model with actual ML predictions
3. **Enhance agents**: Add more sophisticated agent logic
4. **Add database**: Store results for historical analysis
5. **Add monitoring**: Prometheus metrics and alerting