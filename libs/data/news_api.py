from __future__ import annotations
from typing import List
from datetime import datetime
from libs.schemas.models import NewsItem
from libs.utils.config import settings
from libs.utils.http import get_json
from libs.utils.limits import news_semaphore

async def get_news_newsapi(symbol: str, start: datetime, end: datetime) -> List[NewsItem]:
    params = {
        "q": symbol,
        "from": start.date().isoformat(),
        "to": end.date().isoformat(),
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 50,
        "apiKey": settings.news_api_key,
    }
    async with news_semaphore:
        data = await get_json(f"{settings.newsapi_base}/everything", params=params)
    articles = data.get("articles", [])
    out: List[NewsItem] = []
    for a in articles:
        try:
            published = datetime.fromisoformat(a["publishedAt"].replace("Z", "+00:00"))
            out.append(NewsItem(
                symbol=symbol,
                published_at=published,
                title=a.get("title", ""),
                summary=a.get("description", ""),
                source=a.get("source", {}).get("name"),
                url=a.get("url"),
            ))
        except Exception:
            continue
    return out[:200]