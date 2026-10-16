"""FastAPI backend. Start from repository root: python -m uvicorn api.main:app."""
from contextlib import asynccontextmanager
import logging
import os
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator

from src.inference import DEFAULT_MODEL_DIR, MAX_TEXT_LENGTH, PhishingDetector

logger = logging.getLogger(__name__)


class PredictRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_TEXT_LENGTH, strict=True)
    explain: bool = True

    @field_validator('text')
    @classmethod
    def reject_blank(cls, value):
        if not value.strip():
            raise ValueError('Email text cannot be blank.')
        return value


class Indicator(BaseModel):
    term: str
    probability_drop: float


class PredictResponse(BaseModel):
    prediction: Literal['phishing', 'legitimate']
    confidence: float = Field(ge=0, le=1)
    phishing_probability: float = Field(ge=0, le=1)
    model: str
    indicators: list[Indicator]
    warning: str | None = None


def create_app(model_dir=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.detector = None
        try:
            chosen_dir = model_dir if model_dir is not None else os.getenv('PHISHING_MODEL_DIR', DEFAULT_MODEL_DIR)
            app.state.detector = PhishingDetector(Path(chosen_dir))
        except Exception:
            logger.exception('Model startup failed. Run the notebook and check the model directory.')
        yield
        app.state.detector = None

    app = FastAPI(title='ITRI625 Phishing Detector', version='1.0.0', lifespan=lifespan)

    @app.get('/health')
    def health():
        detector = app.state.detector
        if detector is None:
            return JSONResponse(status_code=503, content={
                'status': 'unavailable', 'model_loaded': False,
                'detail': 'Model unavailable. Run the notebook and check server logs.'})
        return {'status': 'ok', 'model_loaded': True, 'model': detector.metadata['selected_model']}

    @app.post('/predict', response_model=PredictResponse)
    def predict(payload: PredictRequest):
        detector = app.state.detector
        if detector is None:
            raise HTTPException(status_code=503, detail='Model unavailable. Run the notebook first.')
        try:
            return detector.predict(payload.text, explain=payload.explain)
        except Exception:
            logger.exception('Prediction failed')
            raise HTTPException(status_code=500, detail='Prediction failed. Check server logs.') from None

    return app


app = create_app()
