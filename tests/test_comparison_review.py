"""Verify blind review preparation for raw comparison outputs."""

import json

from triage_poc.comparison_review import prepare_raw_comparison_review


def _scenario(identifier):
    return {
        "id": identifier,
        "synthetic": True,
        "reference_status": "proposed_educational_only",
        "expected_level": "moderate",
        "category": "other",
        "request": {
            "language": "fr",
            "patient_context": {"symptoms": ["symptôme synthétique"]},
        },
    }


def _output(identifier, level="moderate"):
    return {
        "id": identifier,
        "output": json.dumps(
            {
                "triage_level": level,
                "summary": "Résumé prudent.",
                "clinical_rationale": ["Contexte incomplet."],
                "missing_information": ["Constantes inconnues."],
                "follow_up_questions": ["Depuis quand ?"],
                "red_flags": [],
            }
        ),
    }


def test_blinds_common_schema_valid_raw_outputs():
    scenarios = [_scenario("one"), _scenario("two")]
    outputs = {name: [_output("one"), _output("two")] for name in ("base", "sft", "dpo")}
    queue, key, coverage = prepare_raw_comparison_review(scenarios, outputs, seed=143)
    assert len(queue) == len(key) == 6
    assert coverage["scenario_records_included"] == 2
    assert coverage["omissions"] == []
    assert all("variant" not in row for row in queue)
    assert {row["variant"] for row in key} == {"base", "sft", "dpo"}


def test_omits_scenario_if_one_variant_has_invalid_schema():
    scenarios = [_scenario("one"), _scenario("two")]
    outputs = {name: [_output("one"), _output("two")] for name in ("base", "sft", "dpo")}
    outputs["dpo"][1]["output"] = "not-json"
    queue, key, coverage = prepare_raw_comparison_review(scenarios, outputs, seed=143)
    assert len(queue) == len(key) == 3
    assert coverage["scenario_records_included"] == 1
    assert coverage["omissions"][0]["scenario_id"] == "two"
    assert coverage["omissions"][0]["failures"][0]["variant"] == "dpo"
