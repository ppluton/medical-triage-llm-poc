"""API contract for the POC; no clinical rule is implemented here."""

from __future__ import annotations

from typing import Literal, Protocol
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

TriageLevel = Literal["maximum", "moderate", "deferred"]
SAFETY_NOTICE = (
    "Cette évaluation est une aide au triage et ne remplace pas un professionnel de santé."
)


class PatientContext(BaseModel):
    age_group: Literal["pediatric", "adult", "older_adult", "unknown"]
    symptoms: list[str] = Field(min_length=1, max_length=20)
    duration: str | None = None
    medical_history: list[str] = []


class TriageRequest(BaseModel):
    language: Literal["fr", "en"]
    patient_context: PatientContext


class ModelResult(BaseModel):
    triage_level: TriageLevel
    summary: str
    clinical_rationale: list[str]
    missing_information: list[str]


class TriageResponse(ModelResult):
    interaction_id: str
    safety_notice: str = SAFETY_NOTICE
    model_version: str


class TriageProvider(Protocol):
    def triage(self, request: TriageRequest) -> tuple[ModelResult, str]: ...


def create_app(provider: TriageProvider | None = None) -> FastAPI:
    app = FastAPI(title="Medical triage POC", version="0.1.0")

    @app.post("/v1/triage", response_model=TriageResponse)
    def triage(request: TriageRequest) -> TriageResponse:
        if provider is None:
            raise HTTPException(
                status_code=503, detail="No model provider configured for this POC."
            )
        result, model_version = provider.triage(request)
        return TriageResponse(
            interaction_id=str(uuid4()), model_version=model_version, **result.model_dump()
        )

    return app


app = create_app()
