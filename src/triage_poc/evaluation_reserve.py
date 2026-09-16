"""Validation and freezing of a synthetic held-out triage reserve."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from triage_poc.api import TriageRequest

EXPECTED_CATEGORIES = frozenset(
    {
        "chest_pain",
        "respiratory_distress",
        "neurological_deficit",
        "pediatric",
        "pregnancy",
        "vulnerability",
        "insufficient_information",
        "contradictory_information",
        "other",
    }
)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _request_digest(row: dict) -> str:
    payload = json.dumps(
        row["request"], ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).casefold()
    return hashlib.sha256(payload.encode()).hexdigest()


def freeze_triage_reserve(reserve_path: Path, development_path: Path) -> dict:
    reserve = json.loads(reserve_path.read_text())
    development = json.loads(development_path.read_text())
    if not isinstance(reserve, list) or len(reserve) != 18:
        raise ValueError("The held-out reserve must contain exactly 18 scenarios.")
    identifiers = [row.get("id") for row in reserve]
    if any(
        not isinstance(value, str) or not value.startswith("reserve-triage-v1-")
        for value in identifiers
    ):
        raise ValueError("Reserve identifiers must use the reserved namespace.")
    if len(set(identifiers)) != len(identifiers):
        raise ValueError("Reserve scenario identifiers must be unique.")

    categories: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    levels: Counter[str] = Counter()
    reserve_digests = set()
    for row in reserve:
        request = row.get("request")
        if (
            row.get("synthetic") is not True
            or row.get("split") != "held_out_project_reserve"
            or row.get("reference_status") != "proposed_educational_only"
            or row.get("category") not in EXPECTED_CATEGORIES
            or row.get("expected_level") not in {"maximum", "moderate", "deferred"}
            or not isinstance(request, dict)
            or request.get("language") not in {"fr", "en"}
            or not isinstance(request.get("patient_context"), dict)
        ):
            raise ValueError("Reserve scenario violates the educational reserve contract.")
        context = request["patient_context"]
        if not isinstance(context.get("symptoms"), list) or not context["symptoms"]:
            raise ValueError("Every reserve scenario requires at least one synthetic symptom.")
        TriageRequest.model_validate(request)
        categories[row["category"]] += 1
        languages[request["language"]] += 1
        levels[row["expected_level"]] += 1
        reserve_digests.add(_request_digest(row))

    if set(categories) != EXPECTED_CATEGORIES or any(count != 2 for count in categories.values()):
        raise ValueError("Every required category must have exactly two reserve scenarios.")
    if languages != {"en": 9, "fr": 9}:
        raise ValueError("The reserve must be balanced 9 FR / 9 EN.")
    if len(reserve_digests) != len(reserve):
        raise ValueError("Reserve requests must be unique.")
    development_ids = {row.get("id") for row in development}
    development_digests = {_request_digest(row) for row in development}
    if set(identifiers) & development_ids or reserve_digests & development_digests:
        raise ValueError("The reserve overlaps the development scenarios.")

    return {
        "manifest_id": "synthetic-triage-held-out-reserve-v1",
        "schema_version": "1.0.0",
        "date": "2026-09-16",
        "status": "frozen_not_evaluated",
        "artifact": {
            "path": str(reserve_path),
            "sha256": sha256(reserve_path),
            "records": len(reserve),
        },
        "development_reference": {
            "path": str(development_path),
            "sha256": sha256(development_path),
            "records": len(development),
        },
        "counts": {
            "categories": dict(sorted(categories.items())),
            "languages": dict(sorted(languages.items())),
            "proposed_levels": dict(sorted(levels.items())),
        },
        "isolation": {
            "identifier_overlap": 0,
            "exact_request_digest_overlap": 0,
            "selection_or_model_outputs_seen": False,
        },
        "clinical_validation": "not_performed",
        "limits": [
            "References are proposed for an educational POC and are not clinical thresholds.",
            "Exact request isolation does not exclude semantic similarity or paraphrases.",
            "The reserve must not influence prompts, checkpoints, hyperparameters, or guardrails.",
        ],
    }
