import json
from pathlib import Path

import pytest

from triage_poc.sft_dataset import (
    SftDatasetError,
    render_sft_conversation,
    render_qwen3_text_dataset,
    render_sft_dataset,
)

SAMPLES = Path(__file__).resolve().parents[1] / "data/samples/synthetic-sft-training-v1.json"


def test_renders_canonical_sft_records_as_conversations():
    record = json.loads(SAMPLES.read_text(encoding="utf-8"))[0]

    rendered = render_sft_conversation(record)

    assert rendered["record_id"] == record["record_id"]
    assert [message["role"] for message in rendered["messages"]] == [
        "system",
        "user",
        "assistant",
    ]
    assert "do not diagnose" in rendered["messages"][0]["content"]
    assert (
        json.loads(rendered["messages"][2]["content"])["safety_notice"]
        == record["sft_target"]["safety_notice"]
    )


def test_rejects_the_isolated_test_split():
    record = json.loads(SAMPLES.read_text(encoding="utf-8"))[0]
    record["split"] = "test"

    with pytest.raises(SftDatasetError, match="isolated test split"):
        render_sft_conversation(record)


def test_rejects_duplicate_identifiers():
    record = json.loads(SAMPLES.read_text(encoding="utf-8"))[0]

    with pytest.raises(SftDatasetError, match="identifiers must be unique"):
        render_sft_dataset([record, record])


def test_renders_qwen3_text_with_explicit_template_markers():
    record = json.loads(SAMPLES.read_text(encoding="utf-8"))[0]

    rendered = render_qwen3_text_dataset([record])

    assert rendered[0]["record_id"] == record["record_id"]
    assert rendered[0]["text"].startswith("<|im_start|>system\n")
    assert "<|im_start|>user\n" in rendered[0]["text"]
    assert "<|im_start|>assistant\n<think>\n\n</think>\n\n" in rendered[0]["text"]
    assert rendered[0]["text"].endswith("<|im_end|>\n")
