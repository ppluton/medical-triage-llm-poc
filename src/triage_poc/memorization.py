"""Select a frozen train-only cohort for an explicitly in-sample diagnostic."""


def select_memorization_rows(train, validation, manifest):
    ids = manifest["record_ids"]
    if len(ids) != 12 or len(set(ids)) != 12:
        raise ValueError("Expected twelve distinct train examples")
    train_by_id = {r["record_id"]: r for r in train}
    held_out = {r["record_id"] for r in validation}
    if any(rid not in train_by_id or rid in held_out for rid in ids):
        raise ValueError("Memorization may only use train records")
    return [train_by_id[rid] for rid in ids]
