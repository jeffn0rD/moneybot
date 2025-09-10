# MoneyBot 🚀

A sophisticated algorithmic trading system leveraging machine learning for financial market analysis and automated trading decisions.

## Overview

MoneyBot is a modular, production-ready trading system designed for:
- **Real-time market data processing** with high-throughput capabilities
- **Advanced ML models** for sentiment analysis and price prediction
- **Backtesting framework** for strategy validation
- **Risk management** with dynamic position sizing
- **Ensemble learning** for improved prediction accuracy

## Architecture

### Apps Layer
- **`apps/orchestrator/`** - FastAPI-based orchestration service with async pipelines
- **`apps/agents/`** - Specialized agents for technical, fundamental, and sentiment analysis
- **`apps/price_model_server/`** - Stub server for external TFT/LSTM price models
- **`apps/model-serving/`** - Dedicated microservices for sentiment and price prediction models
- **`apps/backtester/`** - Comprehensive backtesting engine with performance analytics

### Libraries Layer
- **`libs/data/`** - Data adapters for Alpha Vantage, NewsAPI, and Financial Modeling Prep
- **`libs/features/`** - Technical indicators, NLP features, and data transformations
- **`libs/models/`** - Model training pipelines and evaluation frameworks
- **`libs/ensemble/`** - Meta-learning algorithms, risk management, and position sizing
- **`libs/nlp/`** - Natural language processing with FinBERT sentiment analysis
- **`libs/utils/`** - Shared utilities, logging, configuration, and robust HTTP clients

### Infrastructure
- **`infra/`** - Docker configurations, deployment scripts, and infrastructure as code
- **`tests/`** - Comprehensive test suite with unit, integration, and performance tests
- **`docs/`** - System documentation and setup guides
- **`models/`** - Trained models storage
- **`mlruns/`** - MLflow experiment tracking and model registry

## Quick Start

### Prerequisites
- Python 3.9+
- Docker & Docker Compose (optional)
- Redis (for caching, optional)
- PostgreSQL (for data storage, optional)
- API keys:
  - ALPHA_VANTAGE_KEY (https://www.alphavantage.co/support/#api-key)
  - NEWS_API_KEY (https://newsapi.org)
  - FMP_API_KEY (https://site.financialmodelingprep.com/developer)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/moneybot.git
cd moneybot
```

2. Create virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
# Core dependencies for API and training
pip install fastapi uvicorn pydantic==2.8.2 anyio pytest httpx pandas numpy scipy scikit-learn lightgbm

# NLP dependencies for FinBERT sentiment analysis
pip install transformers torch --extra-index-url https://download.pytorch.org/whl/cpu
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys:
# ALPHA_VANTAGE_KEY=your_key_here
# NEWS_API_KEY=your_key_here
# FMP_API_KEY=your_key_here
# 
# Optional Redis configuration:
# REDIS_URL=redis://localhost:6379/0
#
# Optional external price model configuration:
# USE_REMOTE_PRICE_MODEL=false
# PRICE_MODEL_URL=http://localhost:9000/predict
```

### Training the Meta-Learner

Train the LightGBM meta-learner model:
```bash
python libs/models/train_meta.py --symbol AAPL --start 2022-01-01 --end 2024-12-31 --horizon 5 --outfile models/meta_lgbm.pkl
```

### Running the System

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

#### Option C: Using Makefile (Recommended for Development)
```bash
# Start services with single command (Redis + orchestrator)
make up

# Stop services
make down
```

Additional make commands:
- `make test` - Run the test suite
- `make train` - Train the meta-learner model
- `make backtest` - Run backtesting
- `make price-model` - Start the external price model server

### Testing the API

Once running, test the API endpoint:
```bash
curl http://localhost:8000/analyze/AAPL?horizon_days=5
```

Expected response structure:
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

### Backtesting

Run a backtest:
```bash
python backtester/engine.py --symbol AAPL --start 2022-01-01 --end 2024-12-31 --horizon 5
```

## How the System Works

### Data Flow
1. **Inputs**: Market data (OHLCV) from Alpha Vantage, News from NewsAPI, Fundamentals from FMP
2. **Feature Engineering**: Technical indicators (RSI/MACD/Bollinger), Fundamental metrics with recency checks, Sentiment analysis with FinBERT
3. **Agents**: Technical, Fundamental, Sentiment, and Price Model agents process features independently
4. **Ensemble**: Meta-learner combines agent outputs using either trained LightGBM model or simple weighted baseline
5. **Orchestrator**: Coordinates the end-to-end pipeline with caching and logging

### Enhanced Fundamentals via FMP
- Pulls company profile, key metrics, and financial statements snapshot
- Converts to standardized FundamentalFeatures with recency_days tracking
- Includes profit margins and revenue growth signals
- Provides graceful fallback when API key is not set

### Sentiment Analysis
- Uses FinBERT (ProsusAI/finbert) from Hugging Face
- Processes news articles in batches for efficiency
- Applies time-decay weighting (newer news weighs more)
- Converts sentiment logits to scores in [-1,1] range

### HTTP Utilities
- Robust HTTP client with retry/backoff functionality
- Rate-limit handling for all API calls (429 responses)
- Shared async get_json helper across all data adapters
- Configurable timeout and retry parameters

### Meta-Learner
- **Training**: Builds dataset with agent outputs as features and realized forward returns as labels
- **Model**: LightGBM classifier predicts probability that forward return > 0
- **Inference**: Automatically uses trained model if available, otherwise falls back to weighted baseline

### Price Model Server (Optional)
- FastAPI service endpoint for external price models
- Ready to be replaced with trained TFT/LSTM models
- Orchestrator can route to it via configuration flag

## Configuration

The system uses a hierarchical configuration approach:
- **Environment variables** for deployment-specific settings
- **YAML configuration files** for application behavior
- **Model configuration** stored in MLflow

## Data Sources

Supported data sources include:
- **Alpha Vantage** - Real-time and historical market data with rate-limit handling
- **NewsAPI** - News articles for sentiment analysis with retry mechanism
- **Financial Modeling Prep** - Fundamental data with recency checks

## Model Pipeline

1. **Data Ingestion** - Real-time data collection with robust HTTP handling
2. **Feature Engineering** - Technical indicators, fundamental metrics, and sentiment features
3. **Agent Processing** - Independent analysis by specialized agents
4. **Ensemble Learning** - Meta-learner combines agent signals
5. **Model Training** - LightGBM classifier with historical data
6. **Model Serving** - RESTful API endpoints for predictions
7. **Strategy Execution** - Automated trading based on model outputs
8. **Performance Tracking** - Real-time monitoring and alerting

## API Documentation

Once running, access the interactive API documentation:
- **Orchestrator API**: http://localhost:8000/docs

## Testing

Run the complete test suite:
```bash
pytest tests/ -v
```

Run specific test categories:
```bash
pytest tests/test_schemas.py -v
pytest tests/test_orchestrator.py -v
```

## Monitoring

The system includes comprehensive monitoring:
- **Structured logging** with trace IDs
- **In-memory caching** with TTL expiration
- **Performance metrics** tracking
- **Error handling** with graceful fallbacks

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Disclaimer

This software is for educational and research purposes only. Trading financial instruments involves substantial risk and may not be suitable for all investors. Past performance does not guarantee future results. Use at your own risk.
## Repository Connection Verified ✅
- Successfully cloned from GitHub
- All files present and accessible
- GitHub integration working correctly
- Ready for new modifications
