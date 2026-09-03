import json
from pathlib import Path

import pytest

from triage_poc.educational_protocol import (
    EducationalProtocolError,
    load_educational_protocol,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]


def _paths():
    return (
        REPOSITORY_ROOT / "configs" / "educational_triage_protocol_v1.json",
        REPOSITORY_ROOT
        / "data"
        / "manifests"
        / "educational_triage_protocol_v1.schema.json",
    )


def test_repository_protocol_is_valid():
    protocol_path, schema_path = _paths()
    protocol = load_educational_protocol(protocol_path, schema_path)

    assert protocol["status"] == "proposed_educational_only"
    assert protocol["clinical_validation"]["performed"] is False
    assert protocol["dataset_plan"]["split_counts"] == {
        "train": 4000,
        "validation": 500,
        "test": 500,
    }


def test_protocol_rejects_claimed_clinical_validation(tmp_path):
    protocol_path, schema_path = _paths()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol["clinical_validation"]["performed"] = True
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps(protocol), encoding="utf-8")

    with pytest.raises(EducationalProtocolError, match="schema validation"):
        load_educational_protocol(invalid_path, schema_path)


def test_protocol_rejects_deferred_for_missing_information(tmp_path):
    protocol_path, schema_path = _paths()
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    protocol["uncertainty_policy"]["deferred_due_to_missing_information_allowed"] = True
    invalid_path = tmp_path / "invalid.json"
    invalid_path.write_text(json.dumps(protocol), encoding="utf-8")

    with pytest.raises(EducationalProtocolError, match="schema validation"):
        load_educational_protocol(invalid_path, schema_path)
