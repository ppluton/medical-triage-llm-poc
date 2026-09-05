"""Matched Base/SFT/DPO evaluation; no clinical scoring or test-set tuning."""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

BASE_MODEL = "unsloth/Qwen3-1.7B-Base"
BASE_REVISION = "e249956c10337100486d07afb77e3eb2b30906b8"
SFT_SHA256 = "3f050ae77a4b66ecf4a254a407a463a046143437198ac5dfbd7922b75b28a940"
VALIDATION_SHA256 = "7118258c5fdbfe47d5c11b5c4e4b2c2600c4ed17a1eb4b806b0bf5f7c2c52296"


def sha256(path: Path) -> str:
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def load_validation(path: Path) -> list[dict]:
    if sha256(path) != VALIDATION_SHA256:
        raise ValueError("Validation artifact checksum differs from the frozen SFT manifest.")
    rows = [json.loads(line) for line in path.read_text().splitlines()]
    validate_conversations(rows)
    if len(rows) != 500:
        raise ValueError("Expected exactly 500 validation records.")
    return rows


def validate_conversations(rows: list[dict]) -> None:
    seen = set()
    for row in rows:
        if not isinstance(row.get("record_id"), str) or row["record_id"] in seen:
            raise ValueError("Missing or duplicate record ID.")
        seen.add(row["record_id"])
        messages = row.get("messages", [])
        if [m.get("role") for m in messages] != ["system", "user", "assistant"]:
            raise ValueError("Expected system/user/assistant conversation.")
        if any(not isinstance(m.get("content"), str) or not m["content"].strip()
               for m in messages):
            raise ValueError("Empty message.")


def select_rows(rows: list[dict], count: int, seed: int) -> list[dict]:
    if not 0 < count <= len(rows):
        raise ValueError("Sample size must be positive and within validation size.")
    return sorted(rows, key=lambda r: hashlib.sha256(
        f"{seed}:{r['record_id']}".encode()).hexdigest())[:count]


def encode_example(tokenizer, messages: list[dict], max_length: int) -> tuple[list[int], int]:
    """Use the SFT tokenizer template and verify the completion boundary exactly."""
    prompt = tokenizer.apply_chat_template(
        messages[:-1], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    full = tokenizer.apply_chat_template(
        messages, tokenize=False, add_generation_prompt=False, enable_thinking=False)
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
    full_ids = tokenizer.encode(full, add_special_tokens=False)
    if full_ids[:len(prompt_ids)] != prompt_ids:
        raise ValueError("Chat template does not preserve the exact prompt token prefix.")
    if len(full_ids) > max_length:
        raise ValueError("Evaluation example exceeds max_length; no silent truncation.")
    if len(full_ids) <= len(prompt_ids) or len(prompt_ids) == 0:
        raise ValueError("Evaluation example has no completion or prompt tokens.")
    return full_ids, len(prompt_ids)


def summarize(rows: list[dict]) -> dict:
    if not rows:
        raise ValueError("Cannot summarize an empty run.")
    groups = defaultdict(list)
    for row in rows:
        for key in ("all", "language:" + row["language"], "source:" + row["source"]):
            groups[key].append(row)
    result = {}
    for key, items in groups.items():
        count = sum(r["completion_tokens"] for r in items)
        nll = sum(r["completion_nll_sum"] for r in items) / count
        all_tokens = sum(r["sequence_tokens"] for r in items)
        if not math.isfinite(nll):
            raise ValueError("Non-finite loss.")
        result[key] = {
            "records": len(items), "completion_tokens": count,
            "completion_nll": nll, "completion_perplexity": math.exp(min(nll, 700)),
            "sequence_nll": sum(r["sequence_nll_sum"] for r in items) / all_tokens,
        }
    return result


def paired_report(variants: dict[str, list[dict]]) -> dict:
    base = {r["record_id"]: r for r in variants["base"]}
    result = {}
    for name, rows in variants.items():
        index = {r["record_id"]: r for r in rows}
        if len(index) != len(rows) or set(index) != set(base):
            raise ValueError("Variant evaluation IDs differ or contain duplicates.")
        improved = 0
        for record_id, row in index.items():
            reference = base[record_id]
            if row["input_sha256"] != reference["input_sha256"]:
                raise ValueError("Variant tokenized inputs differ.")
            improved += row["completion_nll_sum"] < reference["completion_nll_sum"]
        result[name] = {"metrics": summarize(rows), "lower_nll_than_base_count": improved}
    return result
