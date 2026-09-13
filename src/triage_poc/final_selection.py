"""Select held-out generation identifiers without inspecting answer content."""

from collections.abc import Iterable
from hashlib import sha256


def select_generation_ids(record_ids: Iterable[str], count: int = 50, seed: int = 42) -> list[str]:
    """Rank unique nonempty identifiers independently of input order or answers."""
    identifiers = list(record_ids)
    if any(not isinstance(identifier, str) or not identifier.strip() for identifier in identifiers):
        raise ValueError("Record identifiers must be nonempty strings")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError("Duplicate record identifiers")
    if type(count) is not int or not 1 <= count <= len(identifiers):
        raise ValueError("Selection count must be an integer within the population")
    if type(seed) is not int:
        raise ValueError("Selection seed must be an integer")
    return sorted(
        identifiers,
        key=lambda identifier: (sha256(f"{seed}:{identifier}".encode()).hexdigest(), identifier),
    )[:count]


def validate_final_freeze(freeze: dict, actual_hashes: dict[str, str]) -> None:
    """Reject an unfrozen protocol or any input changed since its explicit freeze."""
    expected = {
        "status": "frozen",
        "split": "test",
        "expected_examples": 500,
        "generation_examples": 50,
        "selection_seed": 42,
        "max_new_tokens": 512,
        "do_sample": False,
        "optimizer_steps": 0,
        "variants": ["base", "sft", "dpo"],
    }
    if any(freeze.get(key) != value for key, value in expected.items()):
        raise ValueError("Explicit final evaluation freeze required")
    if not actual_hashes or freeze.get("input_hashes") != actual_hashes:
        raise ValueError("Final evaluation inputs differ from frozen hashes")
    versions = freeze.get("package_versions")
    if (
        not isinstance(versions, dict)
        or set(versions) != {"torch", "transformers", "peft", "bitsandbytes"}
        or any(not isinstance(value, str) or not value for value in versions.values())
    ):
        raise ValueError("Exact final runtime package versions required")
