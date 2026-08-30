import json
import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "scripts/prepare_sft_dataset.py"
SAMPLES = REPOSITORY_ROOT / "data/samples/synthetic-sft-training-v1.json"


def test_prepare_script_keeps_requested_split_isolated(tmp_path):
    output = tmp_path / "train.jsonl"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(SAMPLES),
            "--split",
            "train",
            "--output",
            str(output),
        ],
        check=True,
        cwd=REPOSITORY_ROOT,
    )

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert [row["record_id"] for row in rows] == ["sft-synthetic-chest-pain-001"]


def test_prepare_script_can_render_preformatted_qwen3_text(tmp_path):
    output = tmp_path / "train.jsonl"

    subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(SAMPLES),
            "--split",
            "train",
            "--format",
            "qwen3-text",
            "--output",
            str(output),
        ],
        check=True,
        cwd=REPOSITORY_ROOT,
    )

    rows = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert rows[0]["text"].startswith("<|im_start|>system\n")
