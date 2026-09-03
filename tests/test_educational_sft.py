from triage_poc.educational_sft import (
    assign_group_splits,
    generate_educational_sft_records,
)


def _candidates():
    records = []
    risks = ("chest_pain", "insufficient_information", "other")
    for index, risk in enumerate(risks):
        group_hash = f"{index + 1:020x}"
        for language in ("fr", "en"):
            records.append(
                {
                    "candidate_id": f"sft-candidate-{group_hash}-{language}",
                    "bilingual_group_id": f"sft-authoring-group-{group_hash}",
                    "requested_language": language,
                    "requested_risk_family": risk,
                    "source": {
                        "source_manifest_id": "src-grounding-fixture",
                        "source_record_id": f"source-{index}",
                    },
                }
            )
    return records


def _protocol():
    return {
        "protocol_id": "educational-triage-protocol-v1",
        "dataset_plan": {
            "total_records": 6,
            "split_counts": {"train": 2, "validation": 2, "test": 2},
        },
    }


def test_assign_group_splits_keeps_bilingual_groups_together():
    group_ids = [candidate["bilingual_group_id"] for candidate in _candidates()]
    assignments = assign_group_splits(
        group_ids,
        {"train": 2, "validation": 2, "test": 2},
        "educational-triage-protocol-v1",
    )

    assert len(assignments) == 3
    assert sorted(assignments.values()) == ["test", "train", "validation"]


def test_generates_proposed_synthetic_records_with_traceability():
    records, summary = generate_educational_sft_records(
        _candidates(),
        _protocol(),
        protocol_sha256="a" * 64,
        code_revision="abcdef1",
        run_id="unit-test",
        dataset_manifest_id="src-educational-sft-protocol-v1",
    )

    assert len(records) == 6
    assert summary["split_counts"] == {"test": 2, "train": 2, "validation": 2}
    assert all(record["data_origin"] == "synthetic" for record in records)
    assert all(
        record["protocol"]["label_status"] == "proposed_protocol_generated" for record in records
    )
    assert all(record["quality"]["clinical_review_status"] == "pending" for record in records)
    assert all(
        record["source"]["source_manifest_id"] == "src-educational-sft-protocol-v1"
        for record in records
    )


def test_missing_information_is_never_deferred():
    records, _ = generate_educational_sft_records(
        _candidates(),
        _protocol(),
        protocol_sha256="a" * 64,
        code_revision="abcdef1",
        run_id="unit-test",
        dataset_manifest_id="src-educational-sft-protocol-v1",
    )

    insufficient = [
        record
        for record in records
        if record["protocol"]["grounding_source_record_id"] == "source-1"
    ]
    assert insufficient
    assert all(record["sft_target"]["triage_level"] == "moderate" for record in insufficient)
