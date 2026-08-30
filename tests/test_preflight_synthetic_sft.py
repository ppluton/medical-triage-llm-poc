import subprocess
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPOSITORY_ROOT / "scripts/preflight_synthetic_sft.py"
SAMPLES = REPOSITORY_ROOT / "data/samples/synthetic-sft-training-v1.json"


def test_synthetic_preflight_accepts_the_explicit_governed_train_split():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--input",
            str(SAMPLES),
            "--manifest",
            "src-synthetic-sft-fixture.json",
            "--split",
            "train",
        ],
        capture_output=True,
        check=False,
        cwd=REPOSITORY_ROOT,
        text=True,
    )

    assert result.returncode == 0
    assert "1 train record" in result.stdout
