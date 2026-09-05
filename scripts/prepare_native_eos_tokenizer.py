#!/usr/bin/env python3
"""Create a local, versioned tokenizer candidate without changing its vocabulary."""
import argparse
import json
from pathlib import Path

from transformers import AutoTokenizer

from triage_poc.comparison import sha256
from triage_poc.sft_termination import native_eos_template


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Preserve existing tokenizers; choose a fresh output")
    tokenizer = AutoTokenizer.from_pretrained(str(args.source), local_files_only=True)
    vocab = tokenizer.get_vocab()
    tokenizer.chat_template = native_eos_template(tokenizer.chat_template)
    tokenizer.save_pretrained(str(args.output))
    reloaded = AutoTokenizer.from_pretrained(str(args.output), local_files_only=True)
    if reloaded.get_vocab() != vocab:
        raise ValueError("Tokenizer vocabulary changed")
    (args.output / "termination-manifest.json").write_text(json.dumps({
        "status": "candidate_not_trained", "vocabulary_unchanged": True,
        "source_template_sha256": sha256(args.source / "chat_template.jinja"),
        "template_sha256": sha256(args.output / "chat_template.jinja"),
        "purpose": "replace_final_assistant_terminator_with_native_eos",
        "eos_token_id": tokenizer.eos_token_id}, indent=2) + "\n")


if __name__ == "__main__":
    main()
