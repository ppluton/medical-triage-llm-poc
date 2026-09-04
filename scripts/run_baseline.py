from pathlib import Path

from triage_poc.baseline import run_baseline

run_baseline(
    "Qwen/Qwen3-1.7B-Base",
    Path("data/samples/synthetic-triage-evaluation-v1.json"),
    Path("artifacts/baseline-qwen3-1.7b.json"),
)
