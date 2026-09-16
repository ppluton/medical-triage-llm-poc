from triage_poc.api import ModelResult
from triage_poc.guardrails import apply_proposed_guardrails, malformed_output_reasons


def _result(level="deferred", summary="Supplied information only.", red_flags=None):
    return ModelResult(
        triage_level=level,
        summary=summary,
        clinical_rationale=[summary],
        missing_information=[],
        red_flags=red_flags or [],
    )


def _context(symptom, **extra):
    return {
        "age_group": "adult",
        "symptoms": [symptom],
        "duration": None,
        "evolution": None,
        "intensity": None,
        "associated_symptoms": [],
        "vulnerability_factors": [],
        "confirmed_absent": [],
        "unavailable_fields": [],
        "medical_history": [],
        "allergies": [],
        "medications": [],
        "vitals": {},
        **extra,
    }


def test_explicit_warning_sign_sets_priority_floor_and_grounded_red_flag():
    context = _context("Severe breathing difficulty, cannot finish a sentence.")
    decision = apply_proposed_guardrails(context, _result("moderate"), "en")
    assert decision.status == "corrected"
    assert decision.result.triage_level == "maximum"
    assert decision.result.red_flags == context["symptoms"]
    assert "explicit_proposed_warning_sign" in decision.reasons


def test_french_neurological_warning_is_detected_despite_intervening_adjective():
    context = _context("Faiblesse soudaine du bras droit et trouble soudain de la parole.")
    decision = apply_proposed_guardrails(context, _result("moderate"), "fr")
    assert decision.result.triage_level == "maximum"
    assert decision.result.red_flags == context["symptoms"]


def test_english_neurological_warning_is_detected_across_separate_symptoms():
    context = _context("sudden weakness of the right arm")
    context["symptoms"].append("difficulty speaking")
    decision = apply_proposed_guardrails(context, _result("moderate"), "en")
    assert decision.result.triage_level == "maximum"
    assert decision.result.red_flags == context["symptoms"]
    assert "explicit_proposed_warning_sign" in decision.reasons


def test_unknown_state_cannot_be_reported_as_stable_or_absent():
    context = _context("I do not feel well.", age_group="unknown")
    decision = apply_proposed_guardrails(
        context,
        _result(summary="The patient is stable and has no warning signs."),
        "en",
    )
    assert decision.status == "safe_fallback"
    assert decision.result.triage_level == "moderate"
    assert "stable" not in decision.result.summary.lower()
    assert "invented_stability_or_absence" in decision.reasons


def test_confirmed_absence_does_not_disable_unrelated_vital_guard():
    context = _context("Mild symptom", confirmed_absent=["associated_symptoms"])
    decision = apply_proposed_guardrails(
        context,
        _result(summary="Vital signs are stable and there are no other symptoms."),
        "en",
    )
    assert decision.status == "safe_fallback"
    assert "invented_vital_stability" in decision.reasons
    assert "invented_absence_of_other_symptoms" not in decision.reasons


def test_stable_sufficiently_described_case_is_not_forced_to_moderate():
    context = _context(
        "Mild wrist discomfort, stable for six months, already assessed, no worsening; "
        "follow-up scheduled."
    )
    result = _result("deferred", summary="Stable supplied symptom; follow-up is scheduled.")
    decision = apply_proposed_guardrails(context, result, "en")
    assert decision.status == "model_output"
    assert decision.result == result


def test_malformed_placeholder_repetition_and_truncation_trigger_fallback():
    malformed = _result(
        "deferred",
        summary="Stable for <DATE_TIME>.",
    ).model_copy(
        update={
            "clinical_rationale": [
                "Repeated clinical phrase repeated clinical phrase "
                "repeated clinical phrase repeated clinical phrase"
            ],
            "missing_information": ["A deliberately long incomplete statement " + "x" * 150],
        }
    )
    reasons = malformed_output_reasons(malformed)
    assert "context_placeholder_in_output" in reasons
    assert "repeated_phrase" in reasons
    assert "likely_truncated_text" in reasons
    decision = apply_proposed_guardrails(_context("Mild symptom"), malformed, "en")
    assert decision.status == "safe_fallback"
