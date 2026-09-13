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
