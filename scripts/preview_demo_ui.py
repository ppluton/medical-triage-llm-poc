#!/usr/bin/env python3
"""Local deterministic UI preview; never calls a model or represents clinical output."""

from triage_poc.api import ModelResult, ProviderResult, TriageRequest, create_app


class SyntheticPreviewProvider:
    prompt_version = "synthetic-ui-preview"

    def triage(self, request: TriageRequest) -> ProviderResult:
        french = request.language == "fr"
        result = ModelResult(
            triage_level="maximum",
            summary=(
                "Scénario synthétique : évaluation professionnelle immédiate requise."
                if french
                else "Synthetic scenario: immediate professional assessment required."
            ),
            clinical_rationale=[
                "Association de symptômes déclarés à vérifier par un professionnel."
                if french
                else "Reported symptom combination requires professional verification."
            ],
            missing_information=(
                ["Constantes vitales mesurées."]
                if french
                else ["Measured vital signs."]
            ),
            follow_up_questions=[],
            red_flags=(
                ["Scénario pédagogique à priorité élevée."]
                if french
                else ["High-priority educational scenario."]
            ),
        )
        return ProviderResult(
            result=result,
            model_version="synthetic-preview-no-model",
            anonymized_input=request,
        )


app = create_app(SyntheticPreviewProvider())
