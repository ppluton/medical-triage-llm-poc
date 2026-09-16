"""Privacy-minimized MLflow tracking for completed SFT and DPO runs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def build_tracking_payload(
    config_path: Path,
    summary_path: Path,
    dataset_manifest_path: Path,
    stage_metrics: dict[str, Path],
) -> dict[str, Any]:
    """Validate run lineage and select only text-free parameters and metrics."""

    config = json.loads(config_path.read_text())
    summary = json.loads(summary_path.read_text())
    dataset = json.loads(dataset_manifest_path.read_text())
    summary_config = summary.get("configuration", config)
    if summary_config.get("dataset_sha256") != config.get("dataset_sha256"):
        raise ValueError("Summary and configuration refer to different datasets.")
    if dataset.get("artifacts", {}).get("canonical", {}).get("sha256") != config.get(
        "dataset_sha256"
    ):
        raise ValueError("Dataset manifest checksum does not match the run configuration.")
    if config.get("test_records_used") != 0 or summary.get("test_records_used", 0) != 0:
        raise ValueError("Training tracking refuses runs that used the test split.")

    params = {
        "experiment_id": config["experiment_id"],
        "base_revision": config["base_revision"],
        "dataset_manifest": config["dataset_manifest"],
        "dataset_sha256": config["dataset_sha256"],
        "seed": config["seed"],
        "learning_rate": config["learning_rate"],
        "max_length": config["max_length"],
        "gradient_accumulation_steps": config["gradient_accumulation_steps"],
        "lora_rank": config["lora"]["rank"],
        "lora_alpha": config["lora"]["alpha"],
        "train_records": config["training_records"],
        "validation_records": config["validation_records"],
    }
    metrics = {
        "optimizer_steps": float(summary.get("optimizer_steps_executed", summary.get("steps", 0))),
        "changed_adapter_tensors": float(summary.get("changed_adapter_tensors", 0)),
    }
    for stage, path in sorted(stage_metrics.items()):
        report = json.loads(path.read_text())
        value = report.get("mean_example_response_nll")
        if not isinstance(value, (int, float)):
            raise ValueError(f"Stage {stage} lacks mean_example_response_nll.")
        metrics[f"{stage}_mean_response_nll"] = float(value)
    return {
        "params": params,
        "metrics": metrics,
        "tags": {
            "run_status": str(summary.get("status", "unknown")),
            "clinical_validation": "not_performed",
            "privacy_scope": "text_free_tracking_only",
        },
        "artifacts": [config_path, summary_path, dataset_manifest_path],
    }


def log_completed_run(
    payload: dict[str, Any],
    tracking_directory: Path,
    *,
    experiment_name: str,
    run_name: str,
    mlflow_module=None,
) -> dict[str, str]:
    """Persist one completed run to a local MLflow file store."""

    if not experiment_name.strip() or not run_name.strip():
        raise ValueError("Experiment and run names are required.")
    tracking_directory.mkdir(parents=True, exist_ok=True)
    artifact_directory = tracking_directory / "artifacts"
    artifact_directory.mkdir(exist_ok=True)
    if mlflow_module is None:
        try:
            import mlflow as mlflow_module
        except ImportError as error:
            raise RuntimeError("Install the project tracking extra before logging.") from error
    database_path = (tracking_directory / "mlflow.db").resolve()
    mlflow_module.set_tracking_uri(f"sqlite:///{database_path}")
    client = mlflow_module.MlflowClient()
    experiment = client.get_experiment_by_name(experiment_name)
    experiment_id = (
        experiment.experiment_id
        if experiment is not None
        else client.create_experiment(
            experiment_name, artifact_location=artifact_directory.resolve().as_uri()
        )
    )
    with mlflow_module.start_run(experiment_id=experiment_id, run_name=run_name) as run:
        mlflow_module.log_params(payload["params"])
        mlflow_module.log_metrics(payload["metrics"])
        mlflow_module.set_tags(payload["tags"])
        for artifact in payload["artifacts"]:
            mlflow_module.log_artifact(str(artifact), artifact_path="evidence")
        return {
            "run_id": run.info.run_id,
            "tracking_uri": mlflow_module.get_tracking_uri(),
            "artifact_uri": mlflow_module.get_artifact_uri(),
        }
