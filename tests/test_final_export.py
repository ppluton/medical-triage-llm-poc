"""Exercise final export on synthetic records, without opening reserved data."""

import json
import runpy
from pathlib import Path

import pytest

from triage_poc.comparison import sha256

export_test = runpy.run_path(
    str(Path(__file__).resolve().parents[1] / "scripts/export_final_test.py")
)["export_test"]


def test_export_links_source_and_preserves_reserved_population(tmp_path):
    records = [
        {
            "record_id": f"synthetic-{i}",
            "task_type": "medical_qa_sft",
            "split": "test" if i < 500 else "train",
            "instruction": "Synthetic prompt",
            "response": "Synthetic answer",
        }
        for i in range(501)
    ]
    canonical = tmp_path / "canonical.jsonl"
    canonical.write_text("\n".join(json.dumps(row) for row in records))
    source = tmp_path / "source.json"
    source.write_text(
        json.dumps({"artifacts": {"canonical": {"sha256": sha256(canonical), "record_count": 501}}})
    )
    original = source.read_bytes()
    result = export_test(canonical, source, tmp_path / "export")
    assert result["record_count"] == 500
    rendered = (tmp_path / "export/test-qwen3.jsonl").read_text().splitlines()
    assert [json.loads(row)["record_id"] for row in rendered] == [
        f"synthetic-{i}" for i in range(500)
    ]
    manifest = json.loads((tmp_path / "export/manifest.json").read_text())
    assert manifest["parent_manifest_sha256"] == sha256(source)
    assert source.read_bytes() == original
    with pytest.raises(ValueError, match="Fresh"):
        export_test(canonical, source, tmp_path / "export")
    canonical.write_text(canonical.read_text() + "\n")
    with pytest.raises(ValueError, match="checksum"):
        export_test(canonical, source, tmp_path / "corrupted")
    assert not (tmp_path / "corrupted").exists()
