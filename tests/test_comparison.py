import pytest

from triage_poc.comparison import encode_example, paired_report, select_rows, summarize


def row(record_id="a", nll=4, tokens=2):
    return {"record_id": record_id, "input_sha256": "same", "language": "fr",
            "source": "synthetic", "completion_nll_sum": nll, "completion_tokens": tokens,
            "sequence_nll_sum": nll + 2, "sequence_tokens": tokens + 2}


def test_token_weighted_metrics_and_paired_identity():
    rows = [row(), row("b", 9, 3)]
    assert summarize(rows)["all"]["completion_nll"] == 13 / 5
    adapted = [row(nll=2), row("b", 8, 3)]
    result = paired_report({"base": rows, "sft": adapted})
    assert result["sft"]["lower_nll_than_base_count"] == 2
    adapted[0]["input_sha256"] = "different"
    with pytest.raises(ValueError, match="inputs differ"):
        paired_report({"base": rows, "sft": adapted})


def test_reject_missing_or_duplicate_variant_records():
    with pytest.raises(ValueError, match="IDs differ"):
        paired_report({"base": [row()], "sft": [row("other")]})
    with pytest.raises(ValueError, match="duplicates"):
        paired_report({"base": [row()], "sft": [row(), row()]})


def test_stable_sampling_does_not_depend_on_file_order():
    rows = [row(str(n)) for n in range(20)]
    assert select_rows(rows, 5, 42) == select_rows(rows[::-1], 5, 42)
    with pytest.raises(ValueError):
        select_rows(rows, 0, 42)


class Tokenizer:
    def apply_chat_template(self, messages, **kwargs):
        return "prompt" if kwargs["add_generation_prompt"] else "promptanswer"

    def encode(self, text, **kwargs):
        return list(text.encode())


def test_completion_mask_excludes_prompt_and_rejects_truncation():
    ids, boundary = encode_example(Tokenizer(), [{}, {}], 20)
    assert bytes(ids[boundary:]) == b"answer"
    with pytest.raises(ValueError, match="no silent truncation"):
        encode_example(Tokenizer(), [{}, {}], 8)
