from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List
import joblib
from pathlib import Path

# Load trained model
model = joblib.load(Path("models/rf_model.pkl").resolve())

print("Model loaded successfully from rf_model.pkl")

app = FastAPI(
    title="CAP 3764 Final Project",
    description="FDOT Construction Risk Analysis Tool",
    version="1.0.0"
)

@app.get("/")
async def main():
    content = """
        <body>
        <h1>CAP 3764 Final Project</h1>
        </body>
        """
    return HTMLResponse(content)

# b-Health check (useful for monitoring and debugging deployment)
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_type": type(model).__name__ if model else None
    }
