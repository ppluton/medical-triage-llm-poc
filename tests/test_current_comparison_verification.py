import importlib.util
import json
from pathlib import Path

import pytest

from triage_poc.comparison import sha256
from triage_poc.triage_probe import score_outputs

spec = importlib.util.spec_from_file_location(
    "comparison_verify", "scripts/verify_current_comparison.py"
)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_recomputes_metrics_and_rejects_missing_or_falsified_observations(tmp_path):
    validation = tmp_path / "validation.jsonl"
    validation.write_text("\n".join(json.dumps({"record_id": str(i)}) for i in range(479)))
    prior = tmp_path / "prior.json"
    prior.write_text(json.dumps({"records": [{"record_id": str(i)} for i in range(30)]}))
    scenarios = Path("data/samples/synthetic-triage-development-v2.json")
    cases = json.loads(scenarios.read_text())
    data = {
        "losses": [{"record_id": str(i), "response_nll": 1.0} for i in range(479)],
        "qa": [{"record_id": str(i), "eos_terminated": True} for i in range(30)],
        "triage": [{"id": r["id"], "output": "invalid"} for r in cases],
    }
    metric = {
        "mean_example_response_nll": 1.0,
        "loss_records": 479,
        "qa_eos_terminated": 30,
        "triage": score_outputs(cases, data["triage"]),
    }
    summary = {
        "status": "completed",
        "optimizer_steps": 0,
        "test_records_used": 0,
        "input_hashes": {
            "validation": sha256(validation),
            "prior_qa": sha256(prior),
            "scenarios": sha256(scenarios),
        },
        "comparison": {s: metric for s in ("base", "sft", "dpo")},
    }
    (tmp_path / "summary.json").write_text(json.dumps(summary))
    for stage in ("base", "sft", "dpo"):
        (tmp_path / f"{stage}.json").write_text(json.dumps(data))
    result = module.verify(tmp_path, validation, prior, scenarios)
    assert result["comparison"]["dpo"]["critical_total"] == 6
    assert result["comparison"]["dpo"]["critical_valid_maximum"] == 0
    data["losses"][0]["response_nll"] = 9.0
    (tmp_path / "dpo.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Summary differs"):
        module.verify(tmp_path, validation, prior, scenarios)
    data["losses"].pop()
    (tmp_path / "dpo.json").write_text(json.dumps(data))
    with pytest.raises(ValueError, match="Missing"):
        module.verify(tmp_path, validation, prior, scenarios)
    validation.write_text(validation.read_text() + "\n")
    with pytest.raises(ValueError, match="checksum"):
        module.verify(tmp_path, validation, prior, scenarios)
