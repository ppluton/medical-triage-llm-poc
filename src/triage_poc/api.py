"""Bounded demonstration API; clinical policies require separate approval."""
from __future__ import annotations

import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal, Protocol
from uuid import uuid4

from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, model_validator

from triage_poc.collection import (
    AbsenceField,
    CollectionField,
    CollectionProgress,
    collection_progress,
    validate_collection_status,
)

TriageLevel = Literal["maximum", "moderate", "deferred"]
Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
SAFETY_NOTICE = (
    "Cette évaluation est une aide au triage et ne remplace pas un professionnel de santé."
)
API_VERSION = "0.4.0"
SAFETY_NOTICES = {
    "fr": SAFETY_NOTICE,
    "en": "This assessment assists triage and does not replace a healthcare professional.",
}


class ProviderFailure(ValueError):
    """A bounded technical category, never a provider's raw exception message."""

    CODES = frozenset({"input_privacy", "input_contract", "transport",
                       "provider_envelope", "generation_incomplete", "generation_length",
                       "generation_content_filter", "generation_tool_calls", "output_contract",
                       "output_privacy", "cleaned_output_contract"})

    def __init__(self, code: str):
        if code not in self.CODES:
            raise ValueError("Unknown provider failure category")
        self.code = code
        super().__init__(code)


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class PatientContext(StrictModel):
    age_group: Literal["pediatric", "adult", "older_adult", "unknown"]
    symptoms: list[Text] = Field(min_length=1, max_length=20)
    duration: Text | None = None
    evolution: Text | None = None
    intensity: Text | None = None
    associated_symptoms: list[Text] = Field(default_factory=list, max_length=20)
    vulnerability_factors: list[Text] = Field(default_factory=list, max_length=20)
    confirmed_absent: list[AbsenceField] = Field(default_factory=list, max_length=5)
    unavailable_fields: list[CollectionField] = Field(default_factory=list, max_length=10)
    medical_history: list[Text] = Field(default_factory=list, max_length=30)
    allergies: list[Text] = Field(default_factory=list, max_length=30)
    medications: list[Text] = Field(default_factory=list, max_length=30)
    vitals: dict[str, float | None] = Field(default_factory=dict, max_length=20)

    @model_validator(mode="after")
    def validate_collection(self):
        validate_collection_status(self.model_dump())
        return self


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
    collection: CollectionProgress
    interaction_id: str
    safety_notice: str = SAFETY_NOTICE
    model_version: str
    latency_ms: float


class ProviderResult(StrictModel):
    result: ModelResult
    model_version: str
    anonymized_input: TriageRequest
    guardrail_status: Literal["model_output", "corrected", "safe_fallback"] = "model_output"
    guardrail_version: str = "unconfigured"
    guardrail_reasons: list[str] = Field(default_factory=list, max_length=20)


class TriageProvider(Protocol):
    def triage(self, request: TriageRequest) -> ProviderResult: ...


class AuditSink(Protocol):
    def write(self, record: dict) -> None: ...


def create_app(provider: TriageProvider | None = None, audit: AuditSink | None = None) -> FastAPI:
    app = FastAPI(title="Medical triage POC", version=API_VERSION)
    demo_directory = Path(__file__).with_name("demo_ui")
    app.mount("/demo", StaticFiles(directory=demo_directory, html=True), name="demo")

    @app.get("/", include_in_schema=False)
    def root():
        return RedirectResponse("/demo/", status_code=307)

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
        content = {}
        try:
            if provider is None:
                raise HTTPException(503, "No model provider configured for this POC.")
            inference = ProviderResult.model_validate(provider.triage(request))
            result, model_version = inference.result, inference.model_version
            status = "schema_validated_not_clinically_validated"
            response = TriageResponse(
                interaction_id=interaction_id, model_version=model_version,
                safety_notice=SAFETY_NOTICES[request.language],
                latency_ms=round((time.perf_counter() - started) * 1000, 2),
                collection=collection_progress(
                    inference.anonymized_input.patient_context.model_dump(), request.language),
                **result.model_dump())
            content = {"anonymized_input": inference.anonymized_input.model_dump(),
                       "output": response.model_dump(), "privacy_status": "passed",
                       "guardrail_status": inference.guardrail_status,
                       "guardrail_version": inference.guardrail_version,
                       "guardrail_reasons": inference.guardrail_reasons}
            return response
        except HTTPException:
            raise
        except ProviderFailure as error:
            status = "provider_or_schema_failure"
            content = {"failure_code": error.code}
            raise HTTPException(502, "Assessment unavailable; contact a healthcare professional.")
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
                        "controls_version": "schema-privacy-collection-guardrails-v5",
                        "status": status,
                        **content,
                        "latency_ms": round((time.perf_counter() - started) * 1000, 2),
                    })
                except Exception:
                    raise HTTPException(503, "Audit unavailable; assessment not delivered.")

    return app


app = create_app()
