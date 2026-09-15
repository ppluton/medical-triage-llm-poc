import argparse
import json
import re
from collections import Counter
from pathlib import Path

from transformers import AutoTokenizer

from triage_poc.sft_authoring_queue import normalize_for_deduplication
from triage_poc.source_sft import render_source_sft_conversation
from triage_poc.source_sft_preflight import validate_source_sft_artifacts

parser = argparse.ArgumentParser(description="Audit frozen SFT artifacts without training")
for name in ["manifest", "artifacts", "tokenizer", "french-train", "mediqal", "output"]:
    parser.add_argument("--" + name, required=True, type=Path)
args = parser.parse_args()
m, canonical, train, val = validate_source_sft_artifacts(args.manifest, args.artifacts)
byid = {r["record_id"]: r for r in canonical}
t = AutoTokenizer.from_pretrained(str(args.tokenizer))
report = {
    "status": "audit_completed",
    "dataset_sha256": m["artifacts"]["canonical"]["sha256"],
    "checks": {},
    "test_rendered_count": 0,
}
report["checks"]["artifacts"] = {
    "hashes": "passed",
    "counts": dict(Counter(r["split"] for r in canonical)),
    "canonical_unique_ids": len(byid),
    "normalized_questions_unique": len(
        {normalize_for_deduplication(r["instruction"]) for r in canonical}
    ),
    "rendered_content_mismatches": sum(
        r != render_source_sft_conversation(byid[r["record_id"]]) for r in train + val
    ),
    "truncated_by_split": dict(
        Counter(r["split"] for r in canonical if r["transformation"]["content_truncated"])
    ),
}
for split, rows in [("train", train), ("validation", val)]:
    lengths = []
    eos = 0
    pad = 0
    end = 0
    for r in rows:
        text = t.apply_chat_template(r["messages"], tokenize=False, add_generation_prompt=False)
        ids = t.encode(text, add_special_tokens=False)
        lengths.append(len(ids))
        eos += t.eos_token_id in ids
        pad += t.pad_token_id in ids
        end += text.endswith("<|im_end|>\n")
    report["checks"][split + "_rendering"] = {
        "records": len(rows),
        "max_tokens": max(lengths),
        "over_2048": sum(n > 2048 for n in lengths),
        "native_eos_present": eos,
        "pad_token_present": pad,
        "assistant_ends_message_end": end,
    }
# Content completeness: inspect only development train/validation source records.
french = json.loads(args.french_train.read_text())
french = {str(r["id"]): r for r in french}
med = args.mediqal
medrows = {}
for category in ["mcqu", "mcqm"]:
    for i, line in enumerate((med / category / "train.json").read_text().splitlines(), 1):
        r = json.loads(line)
        medrows[f"{category}/train.json:{str(r.get('id') or '').strip() or i}"] = r
stats = Counter()
samples = []
for c in canonical:
    if c["split"] == "test":
        continue
    src = c["source"]["source_dataset"]
    if src == "qanastek/frenchmedmcqa":
        raw = french[c["source"]["source_record_id"]]
        options = [str(v).strip() for v in raw["answers"].values() if str(v).strip()]
    elif src == "ANR-MALADES/MediQAl":
        raw = medrows[c["source"]["source_locator"]]
        options = [
            str(raw.get("answer_" + k, "")).strip()
            for k in "abcde"
            if str(raw.get("answer_" + k, "")).strip()
        ]
    else:
        continue
    stats["mcq_records"] += 1
    missing = [o for o in options if o not in c["instruction"]]
    stats["records_with_missing_options"] += bool(missing)
    if (
        re.search(
            r"(suivant|ci.dessous|proposition|lesquell|laquell|parmi)", str(raw["question"]), re.I
        )
        and missing
    ):
        stats["deictic_question_and_missing_options"] += 1
        if len(samples) < 6:
            samples.append(c["record_id"])
report["checks"]["mcq_context"] = {
    **stats,
    "review_sample_ids": samples,
    "limitation": ("Pattern flags require content review; omission alone does not "
                   "make every converted QA invalid."),
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n")
print(json.dumps(report, indent=2))
