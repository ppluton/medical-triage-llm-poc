"""Conservative deterministic guardrails for the educational triage demonstration."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from triage_poc.api import ModelResult, TriageLevel

GUARDRAIL_VERSION = "proposed-guardrails-v3"
_SEVERITY: dict[TriageLevel, int] = {"deferred": 0, "moderate": 1, "maximum": 2}


@dataclass(frozen=True)
class GuardrailResult:
    result: ModelResult
    status: str
    reasons: tuple[str, ...]


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"\s+", " ", value).strip()


def _context_text(context: dict) -> str:
    values = [
        *context.get("symptoms", []),
        *context.get("associated_symptoms", []),
        *context.get("vulnerability_factors", []),
        context.get("duration") or "",
        context.get("evolution") or "",
        context.get("intensity") or "",
    ]
    return _normalize(" ".join(values))


def _result_text(result: ModelResult) -> str:
    return _normalize(
        " ".join(
            [
                result.summary,
                *result.clinical_rationale,
                *result.missing_information,
                *result.follow_up_questions,
                *result.red_flags,
            ]
        )
    )


def _result_values(result: ModelResult) -> list[str]:
    return [
        result.summary,
        *result.clinical_rationale,
        *result.missing_information,
        *result.follow_up_questions,
        *result.red_flags,
    ]


def explicit_warning_signs(context: dict) -> list[str]:
    """Return supplied symptom strings matching the bounded proposed warning policy."""
    symptoms = [*context.get("symptoms", []), *context.get("associated_symptoms", [])]
    combined = _normalize(" ".join(symptoms))
    intensity = _normalize(context.get("intensity") or "")
    chest_cluster = (
        "chest pain" in combined or "douleur thoracique" in combined
    ) and any(
        token in intensity
        for token in ("intense", "forte", "severe", "strong")
    )
    neurological_cluster = (
        any(token in combined for token in ("sudden", "soudaine", "soudain"))
        and (
            "arm weakness" in combined
            or ("weakness" in combined and "arm" in combined)
            or ("faiblesse" in combined and "bras" in combined)
        )
        and any(
            token in combined
            for token in (
                "speech difficulty",
                "difficulty speaking",
                "trouble soudain de la parole",
                "trouble de la parole",
            )
        )
    )
    matches = []
    for symptom in symptoms:
        text = _normalize(symptom)
        chest = ("chest pain" in text or "douleur thoracique" in text) and any(
            token in text for token in ("intense", "persistent", "persistante", "severe")
        )
        breathing = (
            "severe breathing difficulty" in text
            or "difficulte respiratoire severe" in text
            or "cannot finish a sentence" in text
            or "ne peut pas finir une phrase" in text
        )
        consciousness = any(
            token in text
            for token in ("altered consciousness", "perte de connaissance", "conscience alteree")
        )
        deterioration = any(
            token in text
            for token in ("severe deterioration", "aggravation severe", "deterioration severe")
        )
        if chest or breathing or consciousness or deterioration:
            matches.append(symptom)
    if neurological_cluster:
        matches.extend(symptoms)
    if chest_cluster:
        matches.extend(symptoms)
    return list(dict.fromkeys(matches))[:2]


def proposed_priority_floor(context: dict) -> tuple[TriageLevel | None, str | None]:
    """Return a conservative floor from the documented educational policy."""
    if explicit_warning_signs(context):
        return "maximum", "explicit_proposed_warning_sign"
    text = _context_text(context)
    uncertainty = (
        context.get("age_group") in {"unknown", "pediatric", "older_adult"}
        or bool(context.get("vulnerability_factors"))
        or any(token in text for token in ("pregnan", "grossesse"))
        or any(
            token in text
            for token in (
                "do not feel well",
                "ne me sens pas bien",
                "then a month ago",
                "puis il y a un mois",
                "deny pain then confirm",
                "nie la douleur puis la confirme",
            )
        )
    )
    return ("moderate", "explicit_uncertainty_or_vulnerability") if uncertainty else (None, None)


def unsupported_claim_reasons(context: dict, result: ModelResult) -> tuple[str, ...]:
    """Detect a bounded set of high-risk assertions contradicted by missing input data."""
    text = _result_text(result)
    reasons = []
    has_vitals = any(value is not None for value in context.get("vitals", {}).values())
    if not has_vitals and any(
        phrase in text
        for phrase in ("vital signs are stable", "stable vital signs", "constantes vitales stables")
    ):
        reasons.append("invented_vital_stability")

    absent = set(context.get("confirmed_absent", []))
    if any(
        phrase in text
        for phrase in (
            "patient is stable",
            "patient est stable",
            "le patient est stable",
            "patient stable",
            "asymptomatic",
            "asymptomatique",
            "no warning signs",
            "no red flags",
            "aucun signe d'alerte",
            "pas de signes de deterioration",
        )
    ):
        reasons.append("invented_stability_or_absence")
    if "associated_symptoms" not in absent and any(
        phrase in text for phrase in ("no other symptoms", "aucun autre symptome")
    ):
        reasons.append("invented_absence_of_other_symptoms")
    if "medical_history" not in absent and not context.get("medical_history") and any(
        phrase in text for phrase in ("patient has a history", "patient a des antecedents")
    ):
        reasons.append("invented_medical_history")
    if "medications" not in absent and not context.get("medications") and any(
        phrase in text for phrase in ("not currently taking", "ne prend aucun traitement")
    ):
        reasons.append("invented_medication_status")
    return tuple(dict.fromkeys(reasons))


def malformed_output_reasons(result: ModelResult) -> tuple[str, ...]:
    """Detect bounded corruption signatures observed in the development run."""
    reasons = []
    for value in _result_values(result):
        if re.search(r"<(?:PERSON|LOCATION|DATE_TIME)>", value):
            reasons.append("context_placeholder_in_output")
        if re.search(r"&#(?:[0-9]+|x[0-9a-f]+);", value, re.IGNORECASE):
            reasons.append("html_entity_in_output")
        normalized = _normalize(value)
        if normalized in {"missing_information", "follow_up_questions", "red_flags"}:
            reasons.append("schema_field_name_as_content")
        words = normalized.split()
        for start in range(max(0, len(words) - 11)):
            phrase = words[start : start + 6]
            if len(phrase) == 6 and words[start + 6 : start + 12] == phrase:
                reasons.append("repeated_phrase")
                break
        if len(value) >= 150 and value[-1].isalnum() and not value.endswith((".", "!", "?")):
            reasons.append("likely_truncated_text")
    return tuple(dict.fromkeys(reasons))


def _safe_fallback(
    context: dict, language: str, floor: TriageLevel | None, warnings: list[str]
) -> ModelResult:
    level: TriageLevel = floor or "moderate"
    if language == "fr":
        if level == "maximum":
            summary = (
                "Un signal d'alerte explicite est présent. Une évaluation professionnelle "
                "immédiate est nécessaire."
            )
            rationale = "Le garde-fou applique le niveau maximal au signal fourni."
        else:
            summary = (
                "Les informations fournies ne permettent pas d'exclure une situation urgente. "
                "Une évaluation professionnelle rapide est nécessaire."
            )
            rationale = "Des informations cliniques essentielles restent inconnues."
        missing = "Informations nécessaires à l'évaluation encore inconnues."
    else:
        if level == "maximum":
            summary = (
                "An explicit warning sign is present. Immediate professional assessment is "
                "required."
            )
            rationale = "The guardrail applies the maximum level to the supplied warning sign."
        else:
            summary = (
                "The supplied information cannot exclude an urgent condition. Prompt professional "
                "assessment is required."
            )
            rationale = "Essential clinical information remains unknown."
        missing = "Information required for assessment remains unknown."
    return ModelResult(
        triage_level=level,
        summary=summary,
        clinical_rationale=[rationale],
        missing_information=[missing],
        follow_up_questions=[],
        red_flags=warnings,
    )


def apply_proposed_guardrails(context: dict, result: ModelResult, language: str) -> GuardrailResult:
    """Apply proposed priority floors and replace known unsupported assertion patterns."""
    warnings = explicit_warning_signs(context)
    floor, floor_reason = proposed_priority_floor(context)
    if warnings and floor == "maximum":
        return GuardrailResult(
            result=_safe_fallback(context, language, floor, warnings),
            status="safe_fallback",
            reasons=(floor_reason or "explicit_proposed_warning_sign",),
        )
    unsupported = unsupported_claim_reasons(context, result)
    malformed = malformed_output_reasons(result)
    reasons = [*unsupported, *malformed]
    if unsupported or malformed:
        if floor_reason:
            reasons.append(floor_reason)
        return GuardrailResult(
            result=_safe_fallback(context, language, floor, warnings),
            status="safe_fallback",
            reasons=tuple(dict.fromkeys(reasons)),
        )

    updated = result.model_copy(deep=True)
    if floor is not None and _SEVERITY[updated.triage_level] < _SEVERITY[floor]:
        updated.triage_level = floor
        reasons.append(floor_reason or "proposed_priority_floor")
    if warnings and updated.red_flags != warnings:
        updated.red_flags = warnings
        reasons.append("red_flags_grounded_from_input")
    return GuardrailResult(
        result=updated,
        status="corrected" if reasons else "model_output",
        reasons=tuple(dict.fromkeys(reasons)),
    )
