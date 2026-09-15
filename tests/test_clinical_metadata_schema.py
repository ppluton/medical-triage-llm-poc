import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = json.loads(
    (ROOT / "data/manifests/clinical_metadata_v1.schema.json").read_text()
)
SAMPLES = json.loads(
    (ROOT / "data/samples/synthetic-clinical-metadata-v1.json").read_text()
)


def test_clinical_metadata_schema_and_synthetic_examples_are_valid():
    Draft202012Validator.check_schema(SCHEMA)
    validator = Draft202012Validator(SCHEMA)

    for sample in SAMPLES:
        validator.validate(sample)


def test_missing_metadata_cannot_hide_populated_clinical_fields():
    invalid = copy.deepcopy(SAMPLES[1])
    invalid["patient_context"]["symptoms"] = ["invented symptom"]

    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(invalid)


def test_confidence_is_bounded():
    invalid = copy.deepcopy(SAMPLES[0])
    invalid["confidence"]["value"] = 1.1

    with pytest.raises(ValidationError):
        Draft202012Validator(SCHEMA).validate(invalid)
