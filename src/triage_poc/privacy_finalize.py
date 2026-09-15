"""Finalize technical privacy controls for a source-derived SFT corpus.

This module deliberately makes a narrow claim: explicit patient-name candidates
are masked and contextual NER alerts receive a documented technical disposition.
It does not certify legal anonymization or clinical validity.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

from triage_poc.source_sft import render_source_sft_conversation

TEXT_FIELDS = ("instruction", "response")
DIRECT_REVIEW_ENTITIES = frozenset({"PATIENT_NAME"})
CONTEXTUAL_ENTITIES = frozenset({"PERSON", "LOCATION", "DATE_TIME"})


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_jsonl(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"Expected an object at {path.name}:{line_number}.")
            rows.append(value)
    return rows


def _write_jsonl(path: Path, rows: list[dict]) -> dict[str, object]:
    content = "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    )
    path.write_text(content, encoding="utf-8")
    return {
        "path": path.name,
        "sha256": hashlib.sha256(content.encode()).hexdigest(),
        "record_count": len(rows),
        "byte_size": len(content.encode()),
    }


def _mask_spans(text: str, findings: list[dict]) -> tuple[str, int]:
    ranges: dict[tuple[int, int], str] = {}
    for finding in findings:
        start, end = finding.get("start"), finding.get("end")
        span = finding.get("span")
        if not isinstance(start, int) or not isinstance(end, int) or not isinstance(span, str):
            raise ValueError("A direct finding lacks a valid span range.")
        if start < 0 or end <= start or end > len(text) or text[start:end] != span:
            raise ValueError("A direct finding does not match the canonical text.")
        ranges[(start, end)] = span

    ordered = sorted(ranges, reverse=True)
    for (left_start, left_end), (right_start, right_end) in zip(ordered, ordered[1:]):
        if right_end > left_start and (right_start, right_end) != (left_start, left_end):
            raise ValueError("Overlapping direct findings cannot be masked safely.")

    output = text
    for start, end in ordered:
        output = output[:start] + "<PATIENT_NAME>" + output[end:]
    return output, len(ordered)


def finalize_sft_privacy(
    canonical_path: Path,
    findings_path: Path,
    output_directory: Path,
    *,
    expected_canonical_sha256: str,
    expected_findings_sha256: str,
    code_revision: str,
    run_id: str,
) -> dict[str, object]:
    """Create a new immutable SFT candidate with explicit names masked.

    Contextual PERSON/LOCATION/DATE_TIME alerts are retained under a public-source
    policy because indiscriminate masking would corrupt medical content. Their
    disposition remains text-free and auditable; external publication stays blocked.
    """

    if output_directory.exists():
        raise ValueError("Choose a fresh output directory.")
    if sha256(canonical_path) != expected_canonical_sha256:
        raise ValueError("Canonical checksum mismatch.")
    if sha256(findings_path) != expected_findings_sha256:
        raise ValueError("Findings checksum mismatch.")
    if not code_revision.strip() or not run_id.strip():
        raise ValueError("Code revision and run ID are required.")

    rows = _read_jsonl(canonical_path)
    by_id: dict[str, dict] = {}
    for row in rows:
        record_id = row.get("record_id")
        if not isinstance(record_id, str) or record_id in by_id:
            raise ValueError("Canonical record IDs must be unique strings.")
        by_id[record_id] = row

    direct_by_field: dict[tuple[str, str], list[dict]] = defaultdict(list)
    contextual_by_record: dict[str, Counter[str]] = defaultdict(Counter)
    direct_entity_counts: Counter[str] = Counter()
    for finding in _read_jsonl(findings_path):
        record_id = finding.get("record_id")
        field = finding.get("field")
        entity = finding.get("entity")
        if record_id not in by_id or field not in TEXT_FIELDS or not isinstance(entity, str):
            raise ValueError("A finding does not reference the canonical corpus.")
        if entity in DIRECT_REVIEW_ENTITIES:
            direct_by_field[(record_id, field)].append(finding)
            direct_entity_counts[entity] += 1
        elif entity in CONTEXTUAL_ENTITIES:
            contextual_by_record[record_id][entity] += 1
        else:
            raise ValueError(f"Unhandled privacy entity: {entity}.")

    output_directory.mkdir(parents=True, mode=0o700)
    output_directory.chmod(0o700)
    transformed: list[dict] = []
    decisions: list[dict] = []
    masked_records: set[str] = set()
    replacements = 0
    split_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    language_counts: Counter[str] = Counter()

    for source_row in rows:
        row = json.loads(json.dumps(source_row))
        record_id = row["record_id"]
        record_replacements = 0
        for field in TEXT_FIELDS:
            row[field], count = _mask_spans(row[field], direct_by_field[(record_id, field)])
            record_replacements += count
        if record_replacements:
            masked_records.add(record_id)
            replacements += record_replacements

        row["schema_version"] = "2.2.0"
        row["transformation"]["pipeline_version"] = "2.2.0"
        row["transformation"]["code_revision"] = code_revision
        row["transformation"]["run_id"] = run_id
        operations = list(row["transformation"]["operations"])
        for operation in (
            "mask_explicit_patient_name_candidates",
            "retain_contextual_ner_candidates_under_public_source_policy",
        ):
            if operation not in operations:
                operations.append(operation)
        row["transformation"]["operations"] = operations
        row["quality"]["pii_anonymization_status"] = "passed_technical_privacy_controls"
        transformed.append(row)

        contextual = contextual_by_record.get(record_id, Counter())
        decisions.append(
            {
                "record_id": record_id,
                "split": row["split"],
                "direct_action": "masked" if record_replacements else "no_direct_detection",
                "direct_replacements": record_replacements,
                "contextual_action": (
                    "retained_under_public_source_policy"
                    if contextual
                    else "no_contextual_detection"
                ),
                "contextual_entity_counts": dict(sorted(contextual.items())),
                "external_publication_status": "blocked_pending_legal_review",
            }
        )
        split_counts[row["split"]] += 1
        source_counts[row["source"]["source_dataset"]] += 1
        language_counts[row["language"]] += 1

    if replacements != sum(direct_entity_counts.values()):
        raise ValueError("Not every direct finding produced one deterministic replacement.")

    artifacts = {
        "canonical": _write_jsonl(output_directory / "source-sft-v2.2.jsonl", transformed),
        "train_qwen3": _write_jsonl(
            output_directory / "train-qwen3.jsonl",
            [render_source_sft_conversation(row) for row in transformed if row["split"] == "train"],
        ),
        "validation_qwen3": _write_jsonl(
            output_directory / "validation-qwen3.jsonl",
            [
                render_source_sft_conversation(row)
                for row in transformed
                if row["split"] == "validation"
            ],
        ),
        "privacy_decisions": _write_jsonl(
            output_directory / "privacy-decisions.jsonl", decisions
        ),
    }
    for path in output_directory.iterdir():
        path.chmod(0o600)

    contextual_records = len(contextual_by_record)
    return {
        "manifest_id": "derived-source-medical-qa-sft-v2.2-privacy-finalized",
        "schema_version": "1.0.0",
        "status": "ready_for_local_educational_sft",
        "date": "2026-09-16",
        "run_id": run_id,
        "code_revision": code_revision,
        "parent": {
            "canonical_sha256": expected_canonical_sha256,
            "findings_sha256": expected_findings_sha256,
        },
        "record_count": len(transformed),
        "triage_label_count": 0,
        "artifacts": artifacts,
        "split_counts": dict(sorted(split_counts.items())),
        "source_counts": dict(sorted(source_counts.items())),
        "language_counts": dict(sorted(language_counts.items())),
        "privacy_review": {
            "technical_status": "passed_for_controlled_educational_training",
            "direct_findings_masked": replacements,
            "direct_records_masked": len(masked_records),
            "direct_entity_counts": dict(sorted(direct_entity_counts.items())),
            "contextual_records_disposed": contextual_records,
            "contextual_policy": "retain_public_medical_context_without_direct_identifier_pattern",
            "external_publication_status": "blocked_pending_legal_and_human_review",
            "rgpd_certification": "not_claimed",
        },
        "training_launched": False,
        "limits": [
            "Technical privacy controls do not establish legal anonymization or RGPD compliance.",
            (
                "Contextual NER candidates were retained to avoid corrupting medical terms "
                "and citations."
            ),
            (
                "The artifact is admitted only for controlled local educational training, "
                "not publication."
            ),
            "No clinical review or validation was performed.",
        ],
    }
