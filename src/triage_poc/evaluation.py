"""Evidence-bounded triage metrics for synthetic or clinically reviewed fixtures."""

from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Literal

TriageLevel = Literal["maximum", "moderate", "deferred"]
_SEVERITY: dict[TriageLevel, int] = {"deferred": 0, "moderate": 1, "maximum": 2}


@dataclass(frozen=True)
class TriageComparison:
    """One prediction compared with a proposed or clinically reviewed reference."""

    expected: TriageLevel
    predicted: TriageLevel


@dataclass(frozen=True)
class TriageMetrics:
    """Aggregate metrics; clinical interpretation requires approved references."""

    total: int
    exact_match_rate: float
    critical_recall: float | None
    under_triage_count: int
    over_triage_count: int
    confusion_matrix: dict[str, dict[str, int]]


def calculate_triage_metrics(comparisons: Iterable[TriageComparison]) -> TriageMetrics:
    """Calculate descriptive metrics without deciding whether they are clinically acceptable."""

    items = list(comparisons)
    if not items:
        raise ValueError("At least one triage comparison is required.")

    _validate_levels(items)
    labels: tuple[TriageLevel, ...] = ("maximum", "moderate", "deferred")
    matrix = {expected: {predicted: 0 for predicted in labels} for expected in labels}
    exact_matches = under_triage = over_triage = critical_total = critical_correct = 0

    for item in items:
        matrix[item.expected][item.predicted] += 1
        if item.expected == item.predicted:
            exact_matches += 1
        if _SEVERITY[item.predicted] < _SEVERITY[item.expected]:
            under_triage += 1
        if _SEVERITY[item.predicted] > _SEVERITY[item.expected]:
            over_triage += 1
        if item.expected == "maximum":
            critical_total += 1
            critical_correct += item.predicted == "maximum"

    return TriageMetrics(
        total=len(items),
        exact_match_rate=exact_matches / len(items),
        critical_recall=(critical_correct / critical_total) if critical_total else None,
        under_triage_count=under_triage,
        over_triage_count=over_triage,
        confusion_matrix=matrix,
    )


def _validate_levels(items: Iterable[TriageComparison]) -> None:
    invalid = Counter(
        level
        for item in items
        for level in (item.expected, item.predicted)
        if level not in _SEVERITY
    )
    if invalid:
        raise ValueError(f"Unsupported triage levels: {', '.join(sorted(invalid))}")
