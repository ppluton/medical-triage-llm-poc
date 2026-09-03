"""Prepare a deterministic, stratified human-review pilot from an SFT authoring queue."""

from __future__ import annotations

import hashlib
from collections import Counter, defaultdict
from collections.abc import Iterable
from typing import Any


def _stable_key(value: str, seed: str) -> str:
    return hashlib.sha256(f"{seed}:{value}".encode()).hexdigest()


def _group_candidates(records: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        if record.get("training_eligible") is not False:
            raise ValueError("Review input must contain only non-trainable candidates.")
        if (
            record.get("split") is not None
            or record.get("draft", {}).get("triage_level") is not None
        ):
            raise ValueError("Review input must not contain a split or triage target.")
        grouped[str(record["bilingual_group_id"])].append(record)

    groups: list[dict[str, Any]] = []
    for group_id, members in grouped.items():
        if len(members) != 2 or {member["requested_language"] for member in members} != {
            "fr",
            "en",
        }:
            raise ValueError(f"Bilingual group is incomplete: {group_id}.")
        sources = {member["source"]["source_dataset"] for member in members}
        risks = {member["requested_risk_family"] for member in members}
        groundings = {
            (
                member["grounding"]["question"],
                member["grounding"]["answer"],
                member["grounding"]["truncated"],
            )
            for member in members
        }
        if len(sources) != 1 or len(risks) != 1 or len(groundings) != 1:
            raise ValueError(f"Bilingual group metadata differs: {group_id}.")
        groups.append(
            {
                "group_id": group_id,
                "members": sorted(members, key=lambda item: item["requested_language"]),
                "source_dataset": next(iter(sources)),
                "risk_family": next(iter(risks)),
            }
        )
    return groups


def select_stratified_groups(
    records: Iterable[dict[str, Any]],
    *,
    group_count: int,
    seed: str,
) -> list[dict[str, Any]]:
    groups = _group_candidates(records)
    if group_count <= 0 or group_count > len(groups):
        raise ValueError("group_count must be positive and no larger than the queue.")

    strata: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for group in groups:
        strata[(group["risk_family"], group["source_dataset"])].append(group)
    for values in strata.values():
        values.sort(key=lambda group: _stable_key(group["group_id"], seed))

    exact_allocations = {
        key: group_count * len(values) / len(groups) for key, values in strata.items()
    }
    allocations = {key: int(value) for key, value in exact_allocations.items()}
    remaining = group_count - sum(allocations.values())
    remainder_order = sorted(
        strata,
        key=lambda key: (
            -(exact_allocations[key] - allocations[key]),
            _stable_key(f"{key[0]}:{key[1]}", seed),
        ),
    )
    for key in remainder_order[:remaining]:
        allocations[key] += 1

    selected = [group for key, count in allocations.items() for group in strata[key][:count]]
    return sorted(selected, key=lambda group: _stable_key(group["group_id"], seed))


def build_review_items(groups: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for group in groups:
        members = group["members"]
        first = members[0]
        items.append(
            {
                "schema_version": "1.0.0",
                "review_item_id": (
                    f"review-{group['group_id'].removeprefix('sft-authoring-group-')}"
                ),
                "bilingual_group_id": group["group_id"],
                "candidate_ids": [member["candidate_id"] for member in members],
                "requested_languages": [member["requested_language"] for member in members],
                "requested_risk_family": group["risk_family"],
                "source": first["source"],
                "grounding": first["grounding"],
                "review": {
                    "source_relevance_status": "pending",
                    "privacy_review_status": "pending",
                    "risk_family_alignment_status": "pending",
                    "authoring_suitability_status": "pending",
                    "reviewer_role": None,
                    "reviewer_id": None,
                    "reviewed_at": None,
                    "notes": None,
                },
                "clinical_validation_status": "not_started",
                "allowed_next_action": "manual_review_only",
            }
        )
    return items


def summarize_review_items(items: Iterable[dict[str, Any]]) -> dict[str, Any]:
    materialized = list(items)
    return {
        "review_item_count": len(materialized),
        "candidate_count": sum(len(item["candidate_ids"]) for item in materialized),
        "source_counts": dict(
            sorted(Counter(item["source"]["source_dataset"] for item in materialized).items())
        ),
        "risk_family_counts": dict(
            sorted(Counter(item["requested_risk_family"] for item in materialized).items())
        ),
        "review_status_counts": dict(
            sorted(
                Counter(
                    item["review"]["source_relevance_status"] for item in materialized
                ).items()
            )
        ),
    }
