"""Generate synthetic, protocol-labelled SFT records for educational experiments."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

LEVEL_BY_VARIANT = {
    "chest_pain": ("maximum", "maximum", "moderate"),
    "respiratory_distress": ("maximum", "maximum", "moderate"),
    "neurological_deficit": ("maximum", "maximum", "moderate"),
    "pediatric": ("maximum", "moderate", "deferred"),
    "pregnancy": ("maximum", "moderate", "deferred"),
    "vulnerability": ("maximum", "moderate", "deferred"),
    "insufficient_information": ("moderate", "moderate", "moderate"),
    "contradictory_information": ("maximum", "moderate", "moderate"),
    "other": ("moderate", "deferred", "deferred"),
}

RISK_COPY = {
    "chest_pain": {
        "fr": ("douleur thoracique", "essoufflement", "douleur thoracique intense et persistante"),
        "en": ("chest pain", "shortness of breath", "persistent intense chest pain"),
    },
    "respiratory_distress": {
        "fr": ("difficulté respiratoire", "gêne respiratoire", "difficulté respiratoire sévère"),
        "en": ("breathing difficulty", "respiratory discomfort", "severe breathing difficulty"),
    },
    "neurological_deficit": {
        "fr": ("faiblesse d'un côté", "trouble de la parole", "déficit neurologique focal brutal"),
        "en": ("one-sided weakness", "speech difficulty", "sudden focal neurological deficit"),
    },
    "pediatric": {
        "fr": ("symptôme aigu chez un enfant", "baisse d'activité", "altération de la conscience"),
        "en": ("acute symptom in a child", "reduced activity", "altered consciousness"),
    },
    "pregnancy": {
        "fr": (
            "symptôme aigu pendant la grossesse",
            "douleur récente",
            "dégradation sévère pendant la grossesse",
        ),
        "en": (
            "acute symptom during pregnancy",
            "recent pain",
            "severe deterioration during pregnancy",
        ),
    },
    "vulnerability": {
        "fr": (
            "symptôme aigu chez une personne vulnérable",
            "faiblesse récente",
            "altération de la conscience",
        ),
        "en": ("acute symptom in a vulnerable person", "recent weakness", "altered consciousness"),
    },
    "insufficient_information": {
        "fr": ("malaise non précisé", "informations manquantes", "gravité impossible à exclure"),
        "en": ("unspecified discomfort", "missing information", "severity cannot be excluded"),
    },
    "contradictory_information": {
        "fr": (
            "symptômes décrits de façon contradictoire",
            "informations à confirmer",
            "signal sévère non exclu",
        ),
        "en": (
            "contradictory symptom report",
            "information requiring confirmation",
            "severe warning sign not excluded",
        ),
    },
    "other": {
        "fr": ("symptôme général", "demande de conseil", "aggravation récente"),
        "en": ("general symptom", "request for guidance", "recent worsening"),
    },
}

LEVEL_COPY = {
    "fr": {
        "maximum": {
            "summary": "Le scénario synthétique contient un signal sévère explicite.",
            "recommendation": (
                "Demander immédiatement une évaluation par un professionnel ou un "
                "service d'urgence selon les consignes locales."
            ),
        },
        "moderate": {
            "summary": "Le scénario synthétique nécessite une évaluation professionnelle rapide.",
            "recommendation": (
                "Compléter les informations manquantes et solliciter rapidement un "
                "professionnel de santé."
            ),
        },
        "deferred": {
            "summary": (
                "Le scénario synthétique est stable, non aigu et sans signal sévère explicite."
            ),
            "recommendation": (
                "Prévoir un suivi professionnel non urgent et réévaluer sans délai en "
                "cas d'aggravation."
            ),
        },
    },
    "en": {
        "maximum": {
            "summary": "The synthetic scenario contains an explicit severe warning sign.",
            "recommendation": (
                "Request immediate assessment by a healthcare professional or emergency "
                "service according to local guidance."
            ),
        },
        "moderate": {
            "summary": "The synthetic scenario requires prompt professional assessment.",
            "recommendation": (
                "Collect the missing information and promptly contact a healthcare professional."
            ),
        },
        "deferred": {
            "summary": (
                "The synthetic scenario is stable, non-acute and has no explicit severe "
                "warning sign."
            ),
            "recommendation": (
                "Arrange non-urgent professional follow-up and reassess promptly if the "
                "situation worsens."
            ),
        },
    },
}

CONTEXT_VARIANTS = {
    "fr": {
        "medical_history": [
            [],
            ["aucun antécédent déclaré"],
            ["antécédents non précisés"],
            ["antécédents à confirmer"],
        ],
        "medications": [
            [],
            ["aucun traitement déclaré"],
            ["traitements non précisés"],
            ["traitements à confirmer"],
        ],
        "allergies": [
            [],
            ["aucune allergie déclarée"],
            ["allergies non précisées"],
            ["allergies à confirmer"],
        ],
    },
    "en": {
        "medical_history": [
            [],
            ["no medical history reported"],
            ["medical history not specified"],
            ["medical history to be confirmed"],
        ],
        "medications": [
            [],
            ["no treatment reported"],
            ["medications not specified"],
            ["medications to be confirmed"],
        ],
        "allergies": [
            [],
            ["no allergy reported"],
            ["allergies not specified"],
            ["allergies to be confirmed"],
        ],
    },
}


def _digest_int(value: str, offset: int = 0) -> int:
    digest = hashlib.sha256(value.encode()).hexdigest()
    return int(digest[offset : offset + 8], 16)


def assign_group_splits(
    group_ids: Iterable[str], split_counts: Mapping[str, int], protocol_id: str
) -> dict[str, str]:
    unique_groups = sorted(
        set(group_ids),
        key=lambda value: hashlib.sha256(f"{protocol_id}:{value}".encode()).hexdigest(),
    )
    if sum(split_counts.values()) != len(unique_groups) * 2:
        raise ValueError("Split counts must cover two records for every bilingual group.")
    if any(count % 2 for count in split_counts.values()):
        raise ValueError("Every split count must preserve complete bilingual groups.")
    assignments: dict[str, str] = {}
    cursor = 0
    for split in ("train", "validation", "test"):
        group_count = split_counts[split] // 2
        for group_id in unique_groups[cursor : cursor + group_count]:
            assignments[group_id] = split
        cursor += group_count
    return assignments


def _synthetic_context(risk: str, language: str, group_id: str, level: str) -> dict[str, Any]:
    symptom, associated, severe = RISK_COPY[risk][language]
    base = _digest_int(group_id)
    age_group = (
        "pediatric"
        if risk == "pediatric"
        else "older_adult"
        if risk == "vulnerability" and base % 2 == 0
        else "adult"
    )
    duration_unit = {
        "fr": {"maximum": "minutes", "moderate": "heures", "deferred": "semaines"},
        "en": {"maximum": "minutes", "moderate": "hours", "deferred": "weeks"},
    }[language][level]
    duration_prefix = {
        "fr": ("depuis", "environ", "près de", "approximativement"),
        "en": ("for", "about", "nearly", "approximately"),
    }[language][_digest_int(group_id, 56) % 4]
    duration = f"{duration_prefix} {base % 97 + 1} {duration_unit}"
    evolution = {
        "fr": ("apparition récente", "aggravation rapportée", "stable", "récurrent", "à confirmer"),
        "en": ("recent onset", "reported worsening", "stable", "recurrent", "to be confirmed"),
    }[language][_digest_int(group_id, 8) % 5]
    intensity = {
        "fr": ("non précisée", "légère", "modérée", "importante"),
        "en": ("not specified", "mild", "moderate", "severe"),
    }[language][_digest_int(group_id, 16) % 4]
    if level == "maximum":
        associated_symptoms = [associated, severe]
    elif level == "moderate":
        associated_symptoms = [associated]
    else:
        associated_symptoms = []
    vulnerability = {
        "pregnancy": ["grossesse" if language == "fr" else "pregnancy"],
        "vulnerability": [
            "vulnérabilité déclarée" if language == "fr" else "reported vulnerability"
        ],
    }.get(risk, [])
    return {
        "age_group": age_group,
        "symptoms": [symptom],
        "duration": duration,
        "evolution": evolution,
        "intensity": intensity,
        "associated_symptoms": associated_symptoms,
        "medical_history": CONTEXT_VARIANTS[language]["medical_history"][
            _digest_int(group_id, 32) % 4
        ],
        "medications": CONTEXT_VARIANTS[language]["medications"][_digest_int(group_id, 40) % 4],
        "allergies": CONTEXT_VARIANTS[language]["allergies"][_digest_int(group_id, 48) % 4],
        "vitals": {
            "heart_rate": None,
            "temperature_c": None,
            "respiratory_rate": None,
            "oxygen_saturation_pct": None,
            "systolic_bp": None,
        },
        "vulnerability_factors": vulnerability,
    }


def _target(risk: str, language: str, level: str) -> dict[str, Any]:
    symptom, associated, severe = RISK_COPY[risk][language]
    if level == "maximum":
        red_flags = [severe]
        rationale = [symptom, severe]
    elif level == "moderate":
        red_flags = []
        rationale = [symptom, associated]
    else:
        red_flags = []
        rationale = [
            symptom,
            "contexte stable décrit" if language == "fr" else "described stable context",
        ]
    missing = (
        [
            "constantes vitales et évolution à confirmer"
            if language == "fr"
            else "vital signs and evolution to confirm"
        ]
        if level != "deferred"
        else []
    )
    return {
        "triage_level": level,
        "summary": LEVEL_COPY[language][level]["summary"],
        "clinical_rationale": rationale,
        "missing_information": missing,
        "red_flags": red_flags,
        "recommendation": LEVEL_COPY[language][level]["recommendation"],
        "safety_notice": (
            "Cette évaluation est une aide au triage et ne remplace pas un professionnel de santé."
            if language == "fr"
            else (
                "This assessment is triage assistance only and does not replace a "
                "healthcare professional."
            )
        ),
    }


def generate_educational_sft_records(
    candidates: list[dict[str, Any]],
    protocol: Mapping[str, Any],
    *,
    protocol_sha256: str,
    code_revision: str,
    run_id: str,
    dataset_manifest_id: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if len(candidates) != protocol["dataset_plan"]["total_records"]:
        raise ValueError("Candidate count does not match the protocol dataset plan.")
    group_ids = [str(candidate["bilingual_group_id"]) for candidate in candidates]
    splits = assign_group_splits(
        group_ids,
        protocol["dataset_plan"]["split_counts"],
        str(protocol["protocol_id"]),
    )

    records: list[dict[str, Any]] = []
    for candidate in candidates:
        group_id = str(candidate["bilingual_group_id"])
        language = str(candidate["requested_language"])
        risk = str(candidate["requested_risk_family"])
        variant = _digest_int(group_id, 24) % len(LEVEL_BY_VARIANT[risk])
        level = LEVEL_BY_VARIANT[risk][variant]
        suffix = group_id.removeprefix("sft-authoring-group-")
        records.append(
            {
                "schema_version": "1.0.0",
                "record_id": f"sft-educational-{suffix}-{language}",
                "task_type": "sft",
                "language": language,
                "data_origin": "synthetic",
                "patient_context": _synthetic_context(risk, language, group_id, level),
                "source": {
                    "source_manifest_id": dataset_manifest_id,
                    "source_record_id": candidate["candidate_id"],
                    "source_dataset": "medical-triage-poc-educational-sft-v1",
                    "source_license": "CC0-1.0",
                    "source_url": None,
                },
                "transformation": {
                    "pipeline_name": "educational_sft_generator",
                    "pipeline_version": "1.0.0",
                    "code_revision": code_revision,
                    "run_id": run_id,
                },
                "protocol": {
                    "protocol_id": protocol["protocol_id"],
                    "protocol_sha256": protocol_sha256,
                    "label_status": "proposed_protocol_generated",
                    "intended_use": "educational_poc_training_only",
                    "scenario_category": risk,
                    "grounding_candidate_id": candidate["candidate_id"],
                    "grounding_source_manifest_id": candidate["source"]["source_manifest_id"],
                    "grounding_source_record_id": candidate["source"]["source_record_id"],
                },
                "quality": {
                    "pii_anonymization_status": "passed",
                    "clinical_review_status": "pending",
                    "safety_review_status": "manual_review_required",
                },
                "split": splits[group_id],
                "sft_target": _target(risk, language, level),
            }
        )

    content_keys = [
        hashlib.sha256(
            json.dumps(
                [record["language"], record["patient_context"], record["sft_target"]],
                ensure_ascii=False,
                sort_keys=True,
            ).encode()
        ).hexdigest()
        for record in records
    ]
    summary = {
        "record_count": len(records),
        "split_counts": dict(sorted(Counter(record["split"] for record in records).items())),
        "language_counts": dict(sorted(Counter(record["language"] for record in records).items())),
        "label_counts": dict(
            sorted(Counter(record["sft_target"]["triage_level"] for record in records).items())
        ),
        "risk_family_counts": dict(
            sorted(Counter(candidate["requested_risk_family"] for candidate in candidates).items())
        ),
        "duplicate_content_count": len(content_keys) - len(set(content_keys)),
        "clinical_review_status_counts": {"pending": len(records)},
    }
    return records, summary
