"""Conservative content-group isolation without moving held-out records into train."""

import hashlib
from collections import defaultdict

from triage_poc.sft_authoring_queue import normalize_for_deduplication


def content_key(kind: str, text: str) -> str:
    return kind + ":" + hashlib.sha256(normalize_for_deduplication(text).encode()).hexdigest()


def isolate_groups(
    records: list[dict], keys: dict[str, list[str]]
) -> tuple[list[dict], list[dict]]:
    """Retain test over validation over train across connected content groups."""
    by_id = {r["record_id"]: r for r in records}
    if len(by_id) != len(records) or set(keys) != set(by_id):
        raise ValueError("Every unique record must have grouping keys")
    parent = {key: key for key in by_id}

    def find(key):
        while parent[key] != key:
            parent[key] = parent[parent[key]]
            key = parent[key]
        return key

    owners = {}
    for rid, group_keys in keys.items():
        for key in group_keys:
            if key in owners:
                parent[find(rid)] = find(owners[key])
            owners[key] = rid
    components = defaultdict(list)
    for rid in by_id:
        components[find(rid)].append(rid)
    rank = {"train": 0, "validation": 1, "test": 2}
    excluded = []
    for ids in components.values():
        priority = max(rank[by_id[rid]["split"]] for rid in ids)
        group_digest = hashlib.sha256("\n".join(sorted(ids)).encode()).hexdigest()
        for rid in ids:
            if rank[by_id[rid]["split"]] < priority:
                excluded.append(
                    {
                        "record_id": rid,
                        "split": by_id[rid]["split"],
                        "reason": "content_group_in_higher_priority_holdout",
                        "group_sha256": group_digest,
                    }
                )
    removed = {r["record_id"] for r in excluded}
    return [r for r in records if r["record_id"] not in removed], excluded


def cross_split_groups(records: list[dict], keys: dict[str, list[str]]) -> int:
    groups = defaultdict(set)
    for row in records:
        for key in keys[row["record_id"]]:
            groups[key].add(row["split"])
    return sum(len(splits) > 1 for splits in groups.values())
