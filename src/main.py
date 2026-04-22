"""
Loads rf_model.pkl and serves inference for the CAP 3764 Final Project's risk proxy model.

Run from `src/`: uvicorn main:app --reload
"""

from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from features import build_feature_frame

# Load the model
_MODEL_PATH = Path("models/rf_model.pkl")
# Load the model
model = joblib.load(_MODEL_PATH.resolve())
# Get the feature names
_feature_names = model.feature_names_in_

# Create the FastAPI app
app = FastAPI(
    title="CAP 3764 Final Project (demo API)",
    description="Minimal backend for FDOT construction risk-proxy inference (academic demo, not production).",
    version="1.0.0",
)


# Define the predict request model
class PredictRequest(BaseModel):
    """Raw fields aligned with FDOT / modeling CSV (see README data dictionary)."""

    fiscal_year: int = Field(..., ge=2023, le=2030, examples=[2026])
    wpp_haz_tp: str = Field(
        ...,
        description="WPPHAZTP single-character code (see risk-proxy phase legend), e.g. 4, 8, A.",
        examples=["4"],
    )
    work_mix_name: str = Field(
        ...,
        description="WPWKMIXN-style label as in training CSV; unknown labels bucket to Other.",
        examples=["RESURFACING"],
    )


class PredictResponse(BaseModel):
    predicted_risk_proxy: float

# Home page route
@app.get("/", response_class=HTMLResponse)
async def main():
    return """<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>CAP 3764 API</title></head>
<body>
<h1>CAP 3764 Final Project</h1>
<p>Demo FastAPI service. See <a href="/docs">/docs</a> for OpenAPI.</p>
</body></html>"""

# Health check route
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_type": type(model).__name__ if model else None,
        "model_path": str(_MODEL_PATH.resolve()),
    }


# Predict route
@app.post("/predict", response_model=PredictResponse)
async def predict(body: PredictRequest):
    try:
        # Build the feature frame
        X = build_feature_frame(
            body.fiscal_year,
            body.wpp_haz_tp,
            body.work_mix_name,
            _feature_names,
        )
    # Handle errors
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    # Predict the risk proxy
    y_hat = model.predict(X)[0]
    return PredictResponse(predicted_risk_proxy=float(y_hat))
