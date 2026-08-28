import json

import pytest

from triage_poc.training_preflight import TrainingPreflightError, require_approved_manifests


def test_preflight_rejects_absent_or_candidate_manifests(tmp_path):
    with pytest.raises(TrainingPreflightError, match="No approved"):
        require_approved_manifests(tmp_path)
    (tmp_path / "src-candidate.json").write_text(json.dumps({"admission_status": "candidate"}))
    with pytest.raises(TrainingPreflightError, match="Non-approved"):
        require_approved_manifests(tmp_path)


def test_preflight_accepts_only_approved_manifests(tmp_path):
    (tmp_path / "src-approved.json").write_text(json.dumps({"admission_status": "approved"}))
    assert require_approved_manifests(tmp_path) == ["src-approved.json"]
