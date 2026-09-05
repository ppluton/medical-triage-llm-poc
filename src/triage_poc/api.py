"""Bounded demonstration API; clinical policies require separate approval."""
from __future__ import annotations

import time
from datetime import UTC, datetime
from typing import Annotated, Literal, Protocol
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

TriageLevel = Literal["maximum", "moderate", "deferred"]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
SAFETY_NOTICE = (
    "Cette évaluation est une aide au triage et ne remplace pas un professionnel de santé."
)
SAFETY_NOTICES = {
    "fr": SAFETY_NOTICE,
    "en": "This assessment assists triage and does not replace a healthcare professional.",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class PatientContext(StrictModel):
    age_group: Literal["pediatric", "adult", "older_adult", "unknown"]
    symptoms: list[Text] = Field(min_length=1, max_length=20)
    duration: Text | None = None
    medical_history: list[Text] = Field(default_factory=list, max_length=30)
    allergies: list[Text] = Field(default_factory=list, max_length=30)
    medications: list[Text] = Field(default_factory=list, max_length=30)
    vitals: dict[str, float | None] = Field(default_factory=dict, max_length=20)


class TriageRequest(StrictModel):
    language: Literal["fr", "en"]
    patient_context: PatientContext


class ModelResult(StrictModel):
    triage_level: TriageLevel
    summary: Text
    clinical_rationale: list[Text] = Field(min_length=1, max_length=20)
    missing_information: list[Text] = Field(max_length=20)
    follow_up_questions: list[Text] = Field(default_factory=list, max_length=10)
    red_flags: list[Text] = Field(default_factory=list, max_length=20)


class TriageResponse(ModelResult):
    interaction_id: str
    safety_notice: str = SAFETY_NOTICE
    model_version: str
    latency_ms: float


class TriageProvider(Protocol):
    def triage(self, request: TriageRequest) -> tuple[ModelResult, str]: ...


class AuditSink(Protocol):
    def write(self, record: dict) -> None: ...


def create_app(provider: TriageProvider | None = None, audit: AuditSink | None = None) -> FastAPI:
    app = FastAPI(title="Medical triage POC", version="0.2.0")

    @app.get("/healthz")
    def health():
        return {"status": "alive", "provider_configured": provider is not None,
                "clinical_validation": "not_performed"}

    @app.post("/v1/triage", response_model=TriageResponse)
    def triage(request: TriageRequest) -> TriageResponse:
        started = time.perf_counter()
        interaction_id = str(uuid4())
        status = "provider_unavailable"
        model_version = None
        try:
            if provider is None:
                raise HTTPException(503, "No model provider configured for this POC.")
            result, model_version = provider.triage(request)
            result = ModelResult.model_validate(result)
            status = "schema_validated_not_clinically_validated"
            return TriageResponse(
                interaction_id=interaction_id, model_version=model_version,
                safety_notice=SAFETY_NOTICES[request.language],
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                **result.model_dump())
        except HTTPException:
            raise
        except Exception:
            status = "provider_or_schema_failure"
            raise HTTPException(502, "Assessment unavailable; contact a healthcare professional.")
        finally:
            if audit is not None:
                try:
                    audit.write({
                        "interaction_id": interaction_id,
                        "timestamp": datetime.now(UTC).isoformat(),
                        "language": request.language, "model_version": model_version,
                        "prompt_version": getattr(provider, "prompt_version", "unconfigured"),
                        "controls_version": "schema-privacy-v2", "status": status,
                        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                    })
                except Exception:
                    raise HTTPException(503, "Audit unavailable; assessment not delivered.")

    return app


app = create_app()
