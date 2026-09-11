"""Paired descriptive pilot metrics, without automatic quality or clinical acceptance."""

import math
import re
import unicodedata
from collections import Counter, defaultdict


def normalize_answer(text):
    return re.sub(r"\W+", "", unicodedata.normalize("NFKC", text).casefold())


def summarize_pilot(cfg, stages, references):
    expected = cfg["evaluation"]["generation_record_ids"]
    if not expected or len(set(expected)) != len(expected):
        raise ValueError("Expected unique frozen generation IDs")
    if any(rid not in references or references[rid]["split"] != "validation" for rid in expected):
        raise ValueError("All references must belong to validation")
    reports = {}
    for stage in ("base", "pilot_end"):
        data = stages[stage]
        loss = data["mean_example_response_nll"]
        if not isinstance(loss, (int, float)) or not math.isfinite(loss):
            raise ValueError("Finite comparable validation loss required")
        rows = data["records"]
        if len(rows) != len(expected) or {r["record_id"] for r in rows} != set(expected):
            raise ValueError("Paired generations do not cover the frozen IDs")
        metrics = Counter()
        by_source = defaultdict(Counter)
        repetition = []
        for row in rows:
            ids = row["generated_token_ids"]
            if not ids or len(ids) > cfg["evaluation"]["max_new_tokens"]:
                raise ValueError("Invalid generated token length")
            ref = references[row["record_id"]]
            src = ref["source"]["source_dataset"]
            exact = normalize_answer(row["output"]) == normalize_answer(ref["response"])
            metrics["records"] += 1
            metrics["native_eos_terminated"] += ids[-1] == 151643
            metrics["reached_token_cap"] += len(ids) == cfg["evaluation"]["max_new_tokens"]
            metrics["exact_normalized_reference_matches"] += exact
            by_source[src]["records"] += 1
            by_source[src]["exact_normalized_reference_matches"] += exact
            grams = Counter(tuple(ids[i : i + 4]) for i in range(len(ids) - 3))
            repetition.append(sum(n - 1 for n in grams.values()) / max(1, sum(grams.values())))
        reports[stage] = {
            "mean_example_response_nll": loss,
            **metrics,
            "mean_repeated_token_4gram_fraction": sum(repetition) / len(repetition),
            "by_source": dict(by_source),
        }
    return {
        "status": "paired_descriptive_metrics_complete_pending_review",
        "stages": reports,
        "response_nll_delta": reports["pilot_end"]["mean_example_response_nll"]
        - reports["base"]["mean_example_response_nll"],
        "full_training_approved": False,
        "clinical_validation": "not_performed",
        "limits": [
            "Exact normalized reference match misses valid paraphrases; inspect outputs.",
            "Shorter outputs alone do not establish improved answer quality.",
            "GPU checkpoint resume and reload must be verified separately.",
        ],
    }
