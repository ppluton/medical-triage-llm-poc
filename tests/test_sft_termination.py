import pytest

from triage_poc.sft_termination import render_training_text


class Tokenizer:
    eos_token = "<|endoftext|>"

    def apply_chat_template(self, messages, **kwargs):
        return "".join("<|im_start|>" + m["role"] + "\n" + m["content"]
                       + "<|im_end|>\n" for m in messages)


ROW = {"record_id": "synthetic-termination", "messages": [
    {"role": "system", "content": "Synthetic educational example."},
    {"role": "user", "content": "Example question?"},
    {"role": "assistant", "content": "Example answer."}]}


def test_only_final_assistant_terminator_changes():
    tokenizer = Tokenizer()
    original = render_training_text(tokenizer, ROW, False)
    repaired = render_training_text(tokenizer, ROW, True)
    assert "<|endoftext|>" not in original
    assert repaired == original.removesuffix("<|im_end|>\n") + "<|endoftext|>"
    assert repaired.count("<|im_end|>") == 2
    assert repaired.count("<|endoftext|>") == 1
    assert "Example answer.<|endoftext|>" in repaired


def test_unexpected_embedded_eos_is_rejected():
    row = {**ROW, "messages": [*ROW["messages"][:-1],
           {"role": "assistant", "content": "Unexpected <|endoftext|> boundary"}]}
    with pytest.raises(ValueError, match="Unexpected native EOS"):
        render_training_text(Tokenizer(), row, True)


def test_template_wrapper_preserves_inference_and_replaces_training_end():
    from jinja2 import Environment

    from triage_poc.sft_termination import native_eos_template

    original = ("{% for m in messages %}<|im_start|>{{ m.role }}\n"
                "{{ m.content }}<|im_end|>\n{% endfor %}"
                "{% if add_generation_prompt %}<|im_start|>assistant\n{% endif %}")
    engine = Environment()
    base = engine.from_string(original)
    candidate = engine.from_string(native_eos_template(original))
    values = {"messages": ROW["messages"], "eos_token": "<|endoftext|>",
              "add_generation_prompt": False}
    expected = base.render(**values).removesuffix("<|im_end|>\n") + "<|endoftext|>"
    assert candidate.render(**values) == expected
    values.update(messages=ROW["messages"][:-1], add_generation_prompt=True)
    assert candidate.render(**values) == base.render(**values)
