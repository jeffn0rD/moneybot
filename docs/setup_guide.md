# MoneyBot Detailed Setup and Run Guide

## 1. Prerequisites

- Python 3.11
- API keys:
  - ALPHA_VANTAGE_KEY: https://www.alphavantage.co/support/#api-key
  - NEWS_API_KEY: https://newsapi.org
  - FMP_API_KEY: https://site.financialmodelingprep.com/developer

## 2. Project Structure Setup

If you haven't already created the project structure, follow these steps:

```bash
# Create project directory
mkdir moneybot
cd moneybot

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Create directory structure
mkdir -p apps/agents apps/price_model_server libs/data libs/features libs/ensemble libs/utils libs/schemas libs/nlp libs/models backtester infra tests docs
```

## 3. Environment Configuration

Create a `.env` file in the project root with your API keys:

```
ALPHA_VANTAGE_KEY=your_alpha_vantage_key
NEWS_API_KEY=your_news_api_key
FMP_API_KEY=your_fmp_key
```

For macOS/Linux, you can also export environment variables directly:

```bash
export ALPHA_VANTAGE_KEY=your_alpha_vantage_key
export NEWS_API_KEY=your_news_api_key
export FMP_API_KEY=your_fmp_key
```

Optional configuration for external price model server:
```
USE_REMOTE_PRICE_MODEL=false
PRICE_MODEL_URL=http://localhost:9000/predict
```

## 4. Dependencies Installation

Install the required dependencies:

```bash
# Core dependencies for API and training
pip install fastapi uvicorn pydantic==2.8.2 anyio pytest httpx pandas numpy scipy scikit-learn lightgbm

# NLP dependencies for FinBERT sentiment analysis
pip install transformers torch --extra-index-url https://download.pytorch.org/whl/cpu
```

Notes:
- If you have a GPU, install torch accordingly from pytorch.org
- On Apple Silicon, you can use torch nightly or cpu wheels

## 5. Verify FinBERT Downloads

The first run will download model weights (~400MB). Ensure you have disk space and internet connectivity.

## 6. Running the Orchestrator API

Start the orchestrator API server:

```bash
uvicorn apps.orchestrator.main:app --reload
```

Test the API in your browser:
- http://localhost:8000/analyze/AAPL?horizon_days=5

You should see a JSON response with decision and agent outputs. If NEWS_API_KEY is set, sentiment will reflect FinBERT scores.

## 7. Running Tests

Execute the test suite:

```bash
pytest -q
```

## 8. Training the Meta-Learner (LightGBM)

Generate training data and train the model:

```bash
python libs/models/train_meta.py --symbol AAPL --start 2022-01-01 --end 2024-12-31 --horizon 5 --outfile models/meta_lgbm.pkl
```

Expected output: Validation AUC printed and model saved to models/meta_lgbm.pkl

After training, inference will automatically try to load `models/meta_lgbm.pkl`. If missing, it falls back to the simple baseline.

## 9. Backtesting

Run a backtest with the CLI entry point:

```bash
python backtester/engine.py --symbol AAPL --start 2022-01-01 --end 2024-12-31 --horizon 5
```

## 10. Optional: Running the External Price Model Server

Start the price model server on port 9000:

```bash
uvicorn apps.price_model_server.main:app --port 9000
```

Then configure the orchestrator to use it by setting environment variables:

```bash
export USE_REMOTE_PRICE_MODEL=true
export PRICE_MODEL_URL=http://localhost:9000/predict
```

Restart the orchestrator to use the remote model.

## 11. Optional: Docker Deployment

Use the Dockerfile.orchestrator and docker-compose.yml to run the API containerized:

```bash
docker-compose up --build
```

Ensure environment variables are passed to the container.

## 12. Model Management

The system will automatically use a trained model if it exists at `models/meta_lgbm.pkl`. 
If no trained model is found, it will fall back to the simple weighted baseline ensemble.

To retrain the model:
1. Delete the existing model file: `rm models/meta_lgbm.pkl`
2. Run the training script again with updated parameters

## 13. System Monitoring

Logs are structured with trace IDs for debugging:
```
2023-01-01 10:00:00 INFO orchestrator trace=AAPL-1234567890 msg=begin analysis
2023-01-01 10:00:05 INFO orchestrator trace=AAPL-1234567890 msg=end analysis
```

## 14. API Endpoints

### GET /analyze/{symbol}
Analyze a symbol and return trading signals

Parameters:
- horizon_days (int, default=5): Forecast horizon in days

Response:
```json
{
  "decision": {
    "symbol": "AAPL",
    "as_of": "2023-01-01T00:00:00Z",
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