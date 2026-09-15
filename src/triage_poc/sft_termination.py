"""Controlled assistant-termination experiment on the archived SFT format."""
from triage_poc.comparison import validate_conversations


def render_training_text(tokenizer, row: dict, native_eos: bool) -> str:
    validate_conversations([row])
    text = tokenizer.apply_chat_template(row["messages"], tokenize=False,
                                         add_generation_prompt=False)
    ending = "<|im_end|>\n"
    if not text.endswith(ending):
        raise ValueError("Unexpected archived assistant terminator")
    if tokenizer.eos_token in text:
        raise ValueError("Unexpected native EOS inside the original conversation")
    if native_eos:
        text = text[:-len(ending)] + tokenizer.eos_token
    return text


def audit_labels(batch, eos_token_id: int, message_end_id: int) -> dict:
    labels = batch["labels"]
    return {"supervised_tokens": int((labels != -100).sum().item()),
            "supervised_native_eos": int((labels == eos_token_id).sum().item()),
            "supervised_message_end": int((labels == message_end_id).sum().item())}


def native_eos_template(original: str) -> str:
    """Preserve prompts and change only the final assistant training terminator."""
    if not original:
        raise ValueError("An archived chat template is required")
    return ("{% set chsa_rendered %}" + original + "{% endset %}"
            "{% if not add_generation_prompt and messages[-1]['role'] == 'assistant' %}"
            "{% if not chsa_rendered.endswith('<|im_end|>\\n') %}"
            "{{ raise_exception('Unexpected archived assistant terminator') }}{% endif %}"
            "{{ chsa_rendered[:-11] + eos_token }}"
            "{% else %}{{ chsa_rendered }}{% endif %}")


def render_prompt_completion(tokenizer, row: dict) -> dict:
    """Split the native-EOS training text at an exact generation-token boundary."""
    full = render_training_text(tokenizer, row, True)
    prompt = tokenizer.apply_chat_template(row["messages"][:-1], tokenize=False,
        add_generation_prompt=True, enable_thinking=False)
    if not full.startswith(prompt) or len(prompt) >= len(full):
        raise ValueError("Training text does not preserve the generation prompt")
    full_ids = tokenizer.encode(full, add_special_tokens=False)
    prompt_ids = tokenizer.encode(prompt, add_special_tokens=False)
    if full_ids[:len(prompt_ids)] != prompt_ids:
        raise ValueError("Prompt token boundary changed during completion rendering")
    return {"prompt": prompt, "completion": full[len(prompt):]}


def validate_completion_labels(labels: list[int], input_ids: list[int], boundary: int) -> dict:
    """Require exactly the reference completion, including EOS, to be supervised."""
    if not 0 < boundary < len(input_ids) or len(labels) != len(input_ids):
        raise ValueError("Invalid completion label boundary or length")
    if any(label != -100 for label in labels[:boundary]):
        raise ValueError("Prompt tokens must not be supervised")
    if labels[boundary:] != input_ids[boundary:]:
        raise ValueError("Completion tokens must all remain supervised")
    return {"prompt_tokens": boundary, "completion_tokens": len(labels) - boundary,
            "supervised_prompt_tokens": 0, "supervised_completion_tokens": len(labels) - boundary}
