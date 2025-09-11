import asyncio

# Tune these for your rate limits and traffic
ALPHA_VANTAGE_CONCURRENCY = 2     # AV free tier is very tight
NEWSAPI_CONCURRENCY = 5
FMP_CONCURRENCY = 3

alpha_semaphore = asyncio.Semaphore(ALPHA_VANTAGE_CONCURRENCY)
news_semaphore = asyncio.Semaphore(NEWSAPI_CONCURRENCY)
fmp_semaphore = asyncio.Semaphore(FMP_CONCURRENCY)