import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from triage_poc.experiment_tracking import build_tracking_payload, log_completed_run


def _write(path, value):
    path.write_text(json.dumps(value))
    return path


def _fixture(tmp_path):
    dataset_sha = "a" * 64
    config = _write(
        tmp_path / "config.json",
        {
            "experiment_id": "fixture-sft",
            "base_revision": "revision",
            "dataset_manifest": "manifest.json",
            "dataset_sha256": dataset_sha,
            "seed": 42,
            "learning_rate": 1e-4,
            "max_length": 2048,
            "gradient_accumulation_steps": 8,
            "lora": {"rank": 16, "alpha": 16},
            "training_records": 2,
            "validation_records": 1,
            "test_records_used": 0,
        },
    )
    summary = _write(
        tmp_path / "summary.json",
        {
            "configuration": {"dataset_sha256": dataset_sha},
            "status": "completed",
            "optimizer_steps_executed": 3,
            "changed_adapter_tensors": 4,
            "test_records_used": 0,
        },
    )
    manifest = _write(
        tmp_path / "manifest.json",
        {"artifacts": {"canonical": {"sha256": dataset_sha}}},
    )
    stage = _write(tmp_path / "base.json", {"mean_example_response_nll": 1.25})
    return config, summary, manifest, stage


def test_builds_text_free_tracking_payload_and_rejects_lineage_drift(tmp_path):
    config, summary, manifest, stage = _fixture(tmp_path)
    payload = build_tracking_payload(config, summary, manifest, {"base": stage})
    assert payload["metrics"]["base_mean_response_nll"] == 1.25
    assert payload["params"]["dataset_sha256"] == "a" * 64
    assert all(Path(path).name != "base.json" for path in payload["artifacts"])
    changed = json.loads(manifest.read_text())
    changed["artifacts"]["canonical"]["sha256"] = "b" * 64
    manifest.write_text(json.dumps(changed))
    with pytest.raises(ValueError, match="manifest checksum"):
        build_tracking_payload(config, summary, manifest, {"base": stage})


def test_logs_to_explicit_local_store_with_fake_mlflow(tmp_path):
    class Run:
        info = SimpleNamespace(run_id="fixture-run")

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return None

    class Mlflow:
        def __init__(self):
            self.uri = None
            self.logged = []
            self.created_experiment = None

        def set_tracking_uri(self, uri):
            self.uri = uri

        def MlflowClient(self):
            return self

        def get_experiment_by_name(self, name):
            self.experiment = name
            return None

        def create_experiment(self, name, *, artifact_location):
            self.created_experiment = (name, artifact_location)
            return "fixture-experiment"

        def start_run(self, *, experiment_id, run_name):
            self.experiment_id = experiment_id
            self.run_name = run_name
            return Run()

        def log_params(self, values):
            self.params = values

        def log_metrics(self, values):
            self.metrics = values

        def set_tags(self, values):
            self.tags = values

        def log_artifact(self, path, *, artifact_path):
            self.logged.append((path, artifact_path))

        def get_tracking_uri(self):
            return self.uri

        def get_artifact_uri(self):
            return "file:///fixture/artifacts"

    config, summary, manifest, stage = _fixture(tmp_path)
    payload = build_tracking_payload(config, summary, manifest, {"base": stage})
    mlflow = Mlflow()
    result = log_completed_run(
        payload,
        tmp_path / "mlruns",
        experiment_name="chsa-poc",
        run_name="fixture",
        mlflow_module=mlflow,
    )
    assert result["run_id"] == "fixture-run"
    assert mlflow.uri.startswith("sqlite:///")
    assert mlflow.uri.endswith("/mlruns/mlflow.db")
    assert mlflow.created_experiment[1].endswith("/mlruns/artifacts")
    assert len(mlflow.logged) == 3
