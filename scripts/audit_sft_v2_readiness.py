#!/usr/bin/env python3
"""Audit source fidelity, exact response token boundaries and content-group isolation."""

import argparse
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

from jsonschema import Draft202012Validator
from transformers import AutoTokenizer

from triage_poc.comparison import sha256
from triage_poc.sft_isolation import content_key, cross_split_groups, isolate_groups
from triage_poc.sft_termination import render_prompt_completion, render_training_text
from triage_poc.source_sft_preflight import validate_source_sft_artifacts


def raw_sources(medquad, mediqal, french):
    sources = {}
    for file in sorted(medquad.glob("*/*.xml")):
        if file.parent.name.startswith(("10_", "11_", "12_")):
            continue
        for n, pair in enumerate(ET.parse(file).getroot().findall(".//QAPair"), 1):
            loc = f"{file.relative_to(medquad)}:{pair.get('pid') or n}"
            sources[("abachaa/MedQuAD", loc)] = {
                "question": (pair.findtext("Question") or "").strip(),
                "answer": (pair.findtext("Answer") or "").strip(),
                "options": [],
                "case": "",
            }
    for kind in ("mcqu", "mcqm"):
        for n, line in enumerate((mediqal / kind / "train.json").read_text().splitlines(), 1):
            r = json.loads(line)
            options = {k.upper(): str(r.get("answer_" + k) or "").strip() for k in "abcde"}
            correct = [
                s.strip().upper() for s in str(r.get("correct_answers", "")).split(",") if s.strip()
            ]
            loc = f"{kind}/train.json:{str(r.get('id') or '').strip() or n}"
            sources[("ANR-MALADES/MediQAl", loc)] = {
                "question": str(r.get("question") or "").strip(),
                "case": str(r.get("clinical_case") or "").strip(),
                "options": [(k, v) for k, v in options.items() if v],
                "correct": correct,
                "invalid_keys": not correct
                or any(k not in options or not options[k] for k in correct),
                "answer": "\n".join(options[k] for k in correct if k in options),
            }
    for r in json.loads((french / "train.json").read_text()):
        options = {k: str(v).strip() for k, v in r["answers"].items()}
        correct = r["correct_answers"]
        sources[("qanastek/frenchmedmcqa", f"train:{r['id']}")] = {
            "question": str(r["question"]).strip(),
            "case": "",
            "options": list(options.items()),
            "correct": correct,
            "invalid_keys": not correct or any(k not in options or not options[k] for k in correct),
            "answer": "\n".join(options[k] for k in correct if k in options),
        }
    return sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in (
        "manifest",
        "artifacts",
        "original-tokenizer",
        "medquad",
        "mediqal",
        "french",
        "output",
    ):
        parser.add_argument("--" + name, type=Path, required=True)
    parser.add_argument("--scan-direct-identifiers", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Use a fresh audit directory")
    manifest, rows, train, val = validate_source_sft_artifacts(
        args.manifest, args.artifacts, audit_candidate=True
    )
    validator = Draft202012Validator(
        json.loads(Path("data/manifests/source_medical_qa_sft_v2.schema.json").read_text())
    )
    sources = raw_sources(args.medquad, args.mediqal, args.french)
    tokenizer = AutoTokenizer.from_pretrained(str(args.original_tokenizer), local_files_only=True)
    checks = Counter()
    flags = []
    mismatches = []
    groups = {}
    for r in rows:
        validator.validate(r)
        src = r["source"]
        raw = sources[(src["source_dataset"], src["source_locator"])]
        rid = r["record_id"]
        keys = [content_key("question", raw["question"])]
        if src["source_dataset"] == "abachaa/MedQuAD":
            keys += [
                content_key("document", src["source_locator"].rsplit(":", 1)[0]),
                content_key("medquad_answer", r["response"]),
            ]
        if raw["case"]:
            keys += [content_key("case", raw["case"])]
        groups[rid] = keys
        if r["split"] == "test":
            continue
        checks["development_records"] += 1
        options = [value for _, value in raw["options"]]
        if len(options) != len(set(options)):
            flags.append({"record_id": rid, "reason": "duplicate_source_option_text"})
        correct = raw.get("correct", [])
        if len(correct) != len(set(correct)):
            flags.append({"record_id": rid, "reason": "duplicate_source_correct_key"})
        if raw.get("invalid_keys"):
            flags.append({"record_id": rid, "reason": "invalid_source_answer_keys"})
        question = "\n\n".join(x for x in (raw["case"], raw["question"]) if x)
        if raw["options"]:
            question += "\n\nOptions:\n" + "\n".join(f"{k}. {v}" for k, v in raw["options"] if v)
            checks["mcq_records"] += 1
        if question != r["instruction"] or raw["answer"] != r["response"]:
            mismatches.append((r, question, raw["answer"]))
        else:
            checks["exact_source_content_matches"] += 1
        if re.search(
            r"\b(?:figure|image|illustration|tableau|graphique)\s+"
            r"(?:ci[- ]dessous|suivant|jointe?)",
            question,
            re.I,
        ):
            flags.append({"record_id": rid, "reason": "possible_missing_visual_context"})
        if any(
            s in r["instruction"] + r["response"]
            for s in ("<|im_start|>", "<|im_end|>", "<|endoftext|>")
        ):
            flags.append({"record_id": rid, "reason": "reserved_control_token_in_content"})
    if mismatches:
        from triage_poc.anonymization import TextAnonymizer
        from triage_poc.source_sft import SOURCE_DIRECT_IDENTIFIER_ENTITIES

        anon = TextAnonymizer(entities=SOURCE_DIRECT_IDENTIFIER_ENTITIES)
        for r, q, a in mismatches:
            aq, aa = anon.anonymize(q, r["language"]), anon.anonymize(a, r["language"])
            if (
                aq.text == r["instruction"]
                and aa.text == r["response"]
                and aq.audit.status == aa.audit.status == "passed"
            ):
                checks["source_matches_after_anonymization_replay"] += 1
            else:
                flags.append(
                    {"record_id": r["record_id"], "reason": "unexplained_source_transformation"}
                )
    if args.scan_direct_identifiers:
        from triage_poc.anonymization import TextAnonymizer
        from triage_poc.source_sft import SOURCE_DIRECT_IDENTIFIER_ENTITIES

        scanner = TextAnonymizer(entities=SOURCE_DIRECT_IDENTIFIER_ENTITIES)
        for r in rows:
            if r["split"] == "test":
                continue
            for field in ("instruction", "response"):
                result = scanner.anonymize(r[field], r["language"])
                checks["direct_identifier_fields_rescanned"] += 1
                if result.text != r[field] or result.audit.status != "passed":
                    flags.append(
                        {"record_id": r["record_id"], "reason": "direct_identifier_rescan_flag"}
                    )
    token_stats = {}
    for split, rendered in [("train", train), ("validation", val)]:
        lengths, completions = [], []
        for row in rendered:
            pair = render_prompt_completion(tokenizer, row)
            full = tokenizer.encode(pair["prompt"] + pair["completion"], add_special_tokens=False)
            prompt = tokenizer.encode(pair["prompt"], add_special_tokens=False)
            assert full == tokenizer.encode(
                render_training_text(tokenizer, row, True), add_special_tokens=False
            )
            assert full[: len(prompt)] == prompt and len(full) > len(prompt)
            assert full[-1] == tokenizer.eos_token_id and full.count(tokenizer.eos_token_id) == 1
            assert tokenizer.pad_token_id not in full and len(full) <= 2048
            lengths.append(len(full))
            completions.append(len(full) - len(prompt))
        token_stats[split] = {
            "records": len(rendered),
            "maximum_tokens": max(lengths),
            "minimum_completion_tokens": min(completions),
            "native_eos_per_record": 1,
            "over_context_limit": 0,
            "exact_prompt_boundaries": len(rendered),
        }
    retained, exclusions = isolate_groups(rows, groups)
    report = {
        "status": "blocked_pending_isolation_or_review"
        if exclusions or flags
        else "technical_audit_passed",
        "input_sha256": manifest["artifacts"]["canonical"]["sha256"],
        "checks": dict(checks),
        "token_checks": token_stats,
        "review_flags": flags,
        "cross_split_content_groups_before": cross_split_groups(rows, groups),
        "proposed_exclusions": len(exclusions),
        "proposed_exclusion_splits": dict(Counter(r["split"] for r in exclusions)),
        "proposed_retained_splits": dict(Counter(r["split"] for r in retained)),
        "cross_split_content_groups_after": cross_split_groups(retained, groups),
        "test_generation_or_answer_review_records": 0,
        "training_steps": 0,
        "clinical_validation": "not_performed",
        "script_sha256": sha256(Path(__file__)),
        "limits": [
            "Grouping is conservative lexical/document isolation, not semantic independence.",
            "Source agreement does not establish medical correctness or absence of all PII.",
        ],
    }
    args.output.mkdir(parents=True)
    for name, data in [
        ("report.json", report),
        ("groups.json", groups),
        ("exclusions.json", exclusions),
    ]:
        (args.output / name).write_text(json.dumps(data, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
