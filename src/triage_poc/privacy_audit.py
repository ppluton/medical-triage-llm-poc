"""Text-private contextual PII audit for versioned medical QA corpora."""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from triage_poc.anonymization import PII_ENTITIES, Analyzer
from triage_poc.source_sft import SOURCE_DIRECT_IDENTIFIER_ENTITIES

TEXT_FIELDS = ("instruction", "response")
DIRECT_ENTITIES = frozenset((*SOURCE_DIRECT_IDENTIFIER_ENTITIES, "PATIENT_NAME"))


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def audit_contextual_pii(
    canonical_path: Path,
    output_directory: Path,
    *,
    analyzer: Analyzer,
) -> dict:
    """Scan every text field and write private findings plus text-free row decisions."""
    if output_directory.exists():
        raise ValueError("Choose a fresh output directory.")
    output_directory.mkdir(parents=True, mode=0o700)
    output_directory.chmod(0o700)
    findings_path = output_directory / "findings-private.jsonl"
    decisions_path = output_directory / "decisions.jsonl"

    entity_counts: Counter[str] = Counter()
    status_counts: Counter[str] = Counter()
    split_counts: Counter[str] = Counter()
    source_counts: Counter[str] = Counter()
    fields_scanned = 0
    records = 0

    with (
        canonical_path.open() as source_stream,
        findings_path.open("x") as findings_stream,
        decisions_path.open("x") as decisions_stream,
    ):
        for line in source_stream:
            if not line.strip():
                continue
            row = json.loads(line)
            record_id = row.get("record_id")
            split = row.get("split")
            language = row.get("language")
            source = row.get("source", {})
            source_manifest_id = source.get("source_manifest_id")
            if (
                not isinstance(record_id, str)
                or split not in {"train", "validation", "test"}
                or language not in {"fr", "en"}
                or not isinstance(source_manifest_id, str)
            ):
                raise ValueError("Canonical row lacks required audit identity fields.")

            per_record: Counter[str] = Counter()
            for field in TEXT_FIELDS:
                text = row.get(field)
                if not isinstance(text, str) or not text.strip():
                    raise ValueError(f"Empty or missing {field} in {record_id}.")
                fields_scanned += 1
                matches = analyzer.analyze(
                    text=text,
                    entities=list(PII_ENTITIES),
                    language=language,
                )
                for match in matches:
                    per_record[match.entity_type] += 1
                    entity_counts[match.entity_type] += 1
                    findings_stream.write(
                        json.dumps(
                            {
                                "record_id": record_id,
                                "split": split,
                                "source_manifest_id": source_manifest_id,
                                "field": field,
                                "entity": match.entity_type,
                                "score": match.score,
                                "span": text[match.start : match.end],
                                "context": text[
                                    max(0, match.start - 100) : min(len(text), match.end + 100)
                                ],
                            },
                            ensure_ascii=False,
                        )
                        + "\n"
                    )

            direct = {key: value for key, value in per_record.items() if key in DIRECT_ENTITIES}
            if direct:
                status = "manual_review_required_direct_identifier"
            elif per_record:
                status = "contextual_review_required"
            else:
                status = "passed_no_contextual_detection"
            decisions_stream.write(
                json.dumps(
                    {
                        "record_id": record_id,
                        "split": split,
                        "source_manifest_id": source_manifest_id,
                        "status": status,
                        "entity_counts": dict(sorted(per_record.items())),
                        "direct_identifier_counts": dict(sorted(direct.items())),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            records += 1
            status_counts[status] += 1
            split_counts[split] += 1
            source_counts[source_manifest_id] += 1

    summary = {
        "status": "contextual_scan_completed_review_not_inferred",
        "input": {
            "path": canonical_path.name,
            "sha256": _sha256(canonical_path),
            "records": records,
        },
        "fields_scanned": fields_scanned,
        "entity_counts": dict(sorted(entity_counts.items())),
        "record_status_counts": dict(sorted(status_counts.items())),
        "split_counts": dict(sorted(split_counts.items())),
        "source_manifest_counts": dict(sorted(source_counts.items())),
        "outputs": {
            "private_findings": {
                "path": findings_path.name,
                "sha256": _sha256(findings_path),
            },
            "text_free_decisions": {
                "path": decisions_path.name,
                "sha256": _sha256(decisions_path),
                "records": records,
            },
        },
        "limits": [
            "Automated NER candidates are not privacy approval or RGPD certification.",
            "Medical terms, eponyms, authors, durations, and locations may be false positives.",
            "Private findings contain source spans and must stay outside the public repository.",
            "Test text is scanned for privacy only and is not used for model selection.",
        ],
    }
    (output_directory / "summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n"
    )
    for output_path in (findings_path, decisions_path, output_directory / "summary.json"):
        output_path.chmod(0o600)
    return summary


def prepare_direct_identifier_review(findings_path: Path, output_path: Path) -> dict:
    """Create a private, reviewable queue from direct-identifier findings only."""
    if output_path.exists():
        raise ValueError("Choose a fresh review output path.")
    output_path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    output_path.parent.chmod(0o700)
    finding_count = 0
    record_ids: set[str] = set()
    entity_counts: Counter[str] = Counter()
    with findings_path.open() as source_stream, output_path.open("x") as output_stream:
        for line in source_stream:
            if not line.strip():
                continue
            finding = json.loads(line)
            if finding.get("entity") not in DIRECT_ENTITIES:
                continue
            required = ("record_id", "split", "source_manifest_id", "field", "span", "context")
            if any(not isinstance(finding.get(key), str) for key in required):
                raise ValueError("Direct finding lacks required review fields.")
            output_stream.write(
                json.dumps(
                    finding
                    | {
                        "review": {
                            "classification": None,
                            "action": None,
                            "rationale": None,
                            "reviewer": None,
                            "reviewed_at": None,
                        }
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
            finding_count += 1
            record_ids.add(finding["record_id"])
            entity_counts[finding["entity"]] += 1
    output_path.chmod(0o600)
    return {
        "status": "direct_identifier_review_pending",
        "findings": finding_count,
        "records": len(record_ids),
        "entity_counts": dict(sorted(entity_counts.items())),
        "output": {"path": output_path.name, "sha256": _sha256(output_path)},
    }
