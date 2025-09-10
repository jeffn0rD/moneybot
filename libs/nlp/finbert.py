from __future__ import annotations
from typing import List
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TextClassificationPipeline
import torch
from libs.schemas.models import NewsItem

_MODEL_NAME = "ProsusAI/finbert"

class FinBertSentiment:
    def __init__(self, device: str | None = None):
        self.tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
        self.model = AutoModelForSequenceClassification.from_pretrained(_MODEL_NAME)
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self.device = 0 if device == "cuda" else -1
        self.pipeline = TextClassificationPipeline(
            model=self.model,
            tokenizer=self.tokenizer,
            return_all_scores=True,
            device=self.device
        )

    def score_articles(self, items: List[NewsItem]) -> List[NewsItem]:
        texts = [(n.title or "") + " " + (n.summary or "") for n in items]
        if not texts:
            return items
        # Batch processing
        preds = self.pipeline(texts, batch_size=16, truncation=True, max_length=256)
        # Each pred is list of dicts for labels: ['positive','neutral','negative']
        for n, scores in zip(items, preds):
            score_map = {s["label"].lower(): float(s["score"]) for s in scores}
            # Convert to a single signed score in [-1,1]
            pos = score_map.get("positive", 0.0)
            neg = score_map.get("negative", 0.0)
            sent_score = pos - neg
            conf = max(pos, neg, score_map.get("neutral", 0.0))
            n.sentiment_score = sent_score
            n.sentiment_confidence = conf
        return items

# Singleton-ish helper
_finbert_instance: FinBertSentiment | None = None

def get_finbert() -> FinBertSentiment:
    global _finbert_instance
    if _finbert_instance is None:
        _finbert_instance = FinBertSentiment()
    return _finbert_instance