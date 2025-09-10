# A small FastAPI model server you can later replace with a real TFT/LSTM
from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

app = FastAPI(title="Price Model Server")

class PredictRequest(BaseModel):
    symbol: str
    as_of: str
    features: dict
    horizon_days: int

class PredictResponse(BaseModel):
    p10: float
    p50: float
    p90: float
    exp_return: float
    direction: str
    confidence: float
    model_version: str = "external_stub_v1"

@app.post("/predict", response_model=PredictResponse)
def predict(req: PredictRequest):
    # Return a simple deterministic mock based on features hash length
    hlen = len(str(req.features))
    p50 = ((hlen % 7) - 3) / 100.0  # -0.03..0.03
    spread = 0.02
    p10 = p50 - spread
    p90 = p50 + spread
    direction = "up" if p50 > 0.002 else "down" if p50 < -0.002 else "flat"
    conf = max(0.1, 1 - (p90 - p10))
    return PredictResponse(
        p10=p10, p50=p50, p90=p90, exp_return=p50, direction=direction, confidence=conf
    )