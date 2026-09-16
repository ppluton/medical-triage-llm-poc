"""Contracts for the one-shot held-out triage reserve evaluation."""

from __future__ import annotations

import json
from pathlib import Path

from triage_poc.evaluation_reserve import freeze_triage_reserve, sha256


def validate_model_selection(decision_path: Path, comparison_summary_path: Path) -> dict:
    """Validate an immutable development-only model selection decision."""
    decision = json.loads(decision_path.read_text())
    comparison = json.loads(comparison_summary_path.read_text())
    if (
        comparison.get("status") != "completed"
        or comparison.get("optimizer_steps") != 0
        or comparison.get("test_records_used") != 0
        or comparison.get("evaluation_split") != "validation"
    ):
        raise ValueError("A completed development-only comparison is required")
    if decision.get("status") != "selected_for_one_shot_reserve":
        raise ValueError("The model selection decision is not final")
    if decision.get("selected_variant") not in {"sft", "dpo"}:
        raise ValueError("The final reserve accepts only the verified SFT or DPO candidate")
    if decision.get("comparison_summary_sha256") != sha256(comparison_summary_path):
        raise ValueError("The selection decision does not match the comparison summary")
    rationale = decision.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        raise ValueError("A documented selection rationale is required")
    if decision.get("held_out_reserve_used") is not False:
        raise ValueError("Selection must precede every held-out reserve observation")
    return decision


def validate_frozen_reserve(
    manifest_path: Path,
    reserve_path: Path,
    development_path: Path,
) -> dict:
    """Recompute the frozen reserve manifest before its one authorized evaluation."""
    expected = json.loads(manifest_path.read_text())
    actual = freeze_triage_reserve(reserve_path, development_path)
    comparable_expected = json.loads(json.dumps(expected))
    comparable_actual = json.loads(json.dumps(actual))
    for section in ("artifact", "development_reference"):
        comparable_expected.get(section, {}).pop("path", None)
        comparable_actual.get(section, {}).pop("path", None)
    if comparable_expected != comparable_actual:
        raise ValueError("The held-out reserve differs from its frozen manifest")
    if (
        actual.get("status") != "frozen_not_evaluated"
        or actual.get("artifact", {}).get("records") != 18
        or actual.get("isolation", {}).get("selection_or_model_outputs_seen") is not False
    ):
        raise ValueError("An untouched eighteen-scenario reserve is required")
    return actual
