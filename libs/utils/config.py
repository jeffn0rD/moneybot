from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Data providers
    alpha_vantage_key: str = Field(default="", alias="ALPHA_VANTAGE_KEY")
    news_api_key: str = Field(default="", alias="NEWS_API_KEY")
    fmp_api_key: str = Field(default="", alias="FMP_API_KEY")

    # Orchestrator
    request_timeout_s: int = 8
    cache_ttl_s: int = 300
    max_retries: int = 2

    # Backtest
    slippage_bps: float = 5.0
    fee_bps: float = 1.0

    # Models
    meta_model_path: str = "models/meta_lgbm.pkl"
    use_remote_price_model: bool = False
    price_model_url: str = "http://localhost:9000/predict"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Providers base URLs
    fmp_base: str = "https://financialmodelingprep.com/api/v3"
    newsapi_base: str = "https://newsapi.org/v2"
    alphavantage_base: str = "https://www.alphavantage.co/query"

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()