# MoneyBot System Overview

## How the System Works

### Inputs
- **Market data (OHLCV)** from Alpha Vantage
- **Fundamentals** from Financial Modeling Prep (FMP)
- **News** from NewsAPI, then FinBERT for per-article sentiment

### Feature Engineering
- **Technical**: RSI/MACD/Bollinger on OHLCV
- **Fundamental**: PE/ROE/D/E, profit margins, revenue growth from FMP financial statements
- **Sentiment**: FinBERT logits → sentiment score per article → time-decayed, source-weighted average

### Agents
- **Technical Agent**: scores signals from tech features
- **Fundamental Agent**: scores valuation/quality with enhanced FMP metrics
- **Sentiment Agent**: scores weighted sentiment
- **Price Model Agent**: emits probabilistic short-horizon forecast (can use remote TFT/LSTM model)

### Ensemble (Meta-learner)
- **Training**: builds dataset with agent outputs (features) and realized forward returns (labels)
- **Model**: LightGBM classifier predicts probability that forward return > 0
- **Inference**: Ensemble reads agent outputs, feeds them to the meta model, gets P(up), then applies a position sizing heuristic

### Orchestrator
- Async endpoint `/analyze/{symbol}` to run the pipeline end-to-end, with caching and logs
- Supports both local stub and remote price model inference

### Backtester
- Walk-forward simulation: calls orchestrator periodically, uses next-bar execution, evaluates equity curve

## Data Flow

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Data Sources  │───▶│  Feature Engine  │───▶│     Agents      │
│                 │    │                  │    │                 │
│ • Alpha Vantage │    │ • Technical      │    │ • Technical     │
│ • News API      │    │ • Fundamental    │    │ • Fundamental   │
│ • FMP API       │    │ • Sentiment      │    │ • Sentiment     │
└─────────────────┘    │ • Model Features │    │ • Price Model   │
                       └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Meta Ensemble  │
                                                │                 │
                                                │ • LightGBM      │
                                                │ • Fallback      │
                                                └─────────────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Orchestrator   │
                                                │                 │
                                                │ • API Endpoint  │
                                                │ • Caching       │
                                                │ • Remote Model  │
                                                └─────────────────┘
```

## HTTP Utilities

The system now includes robust HTTP utilities with:
- **Retry mechanism** with exponential backoff
- **Rate-limit handling** for 429 responses
- **Timeout management** for all API calls
- **Error handling** with custom HttpError exceptions

## FMP Fundamentals Adapter

The new FMP adapter provides:
- **Company profile** data
- **Key metrics** from financial statements
- **Income statement** and **balance sheet** data
- **Recency checks** to ensure data freshness
- **Fallback behavior** when API key is not provided

## Price Model Server

An optional FastAPI service endpoint for external price models:
- Ready to be replaced with trained TFT/LSTM models
- Provides probabilistic forecasts with confidence intervals
- Orchestrator can route to it via configuration flag

## Next Steps for Enhancement

1. **Add Redis** for caching and MLflow for experiment tracking
2. **Enhance feature set** with additional technical indicators (ATR, SMA/EMA, volatility)
3. **Include market regime features** (VIX, rates) in meta-model
4. **Improve label definition** and frequency (e.g., overlapping windows with careful leakage avoidance)
5. **Add more sophisticated risk management** and position sizing algorithms