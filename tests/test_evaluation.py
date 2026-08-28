import pytest

from triage_poc.evaluation import TriageComparison, calculate_triage_metrics


def test_calculates_exact_critical_under_and_over_triage_metrics():
    metrics = calculate_triage_metrics(
        [
            TriageComparison(expected="maximum", predicted="maximum"),
            TriageComparison(expected="maximum", predicted="moderate"),
            TriageComparison(expected="moderate", predicted="deferred"),
            TriageComparison(expected="deferred", predicted="moderate"),
        ]
    )

    assert metrics.total == 4
    assert metrics.exact_match_rate == 0.25
    assert metrics.critical_recall == 0.5
    assert metrics.under_triage_count == 2
    assert metrics.over_triage_count == 1
    assert metrics.confusion_matrix["maximum"] == {
        "maximum": 1,
        "moderate": 1,
        "deferred": 0,
    }


def test_returns_no_critical_recall_when_fixture_has_no_maximum_case():
    metrics = calculate_triage_metrics(
        [TriageComparison(expected="moderate", predicted="moderate")]
    )

    assert metrics.critical_recall is None


def test_rejects_empty_or_unknown_levels():
    with pytest.raises(ValueError, match="At least one"):
        calculate_triage_metrics([])
    with pytest.raises(ValueError, match="Unsupported"):
        calculate_triage_metrics([TriageComparison(expected="other", predicted="maximum")])
