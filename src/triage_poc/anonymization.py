"""Fail-closed text de-identification for the educational POC.

The module removes detected PII from text before it can enter a local data
pipeline. It does not establish legal compliance or clinical validation.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from presidio_analyzer import AnalyzerEngine, Pattern, PatternRecognizer, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_analyzer.predefined_recognizers import EmailRecognizer
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig
from tldextract import TLDExtract

SUPPORTED_LANGUAGES = frozenset({"fr", "en"})
PII_ENTITIES = (
    "PERSON",
    "PHONE_NUMBER",
    "EMAIL_ADDRESS",
    "CREDIT_CARD",
    "IBAN_CODE",
    "IP_ADDRESS",
    "LOCATION",
    "DATE_TIME",
    "PATIENT_REFERENCE",
)


class AnonymizationConfigurationError(RuntimeError):
    """Raised when the detector cannot safely process the requested text."""


class Analyzer(Protocol):
    """Minimal Presidio-compatible detector interface for testability."""

    def analyze(
        self, *, text: str, entities: Sequence[str], language: str
    ) -> list[RecognizerResult]: ...


class Anonymizer(Protocol):
    """Minimal Presidio-compatible anonymizer interface for testability."""

    def anonymize(
        self,
        *,
        text: str,
        analyzer_results: Sequence[RecognizerResult],
        operators: dict[str, OperatorConfig],
    ): ...


@dataclass(frozen=True)
class AnonymizationAudit:
    """PII-free audit metadata. Original text and spans are intentionally absent."""

    language: str
    detected_entity_counts: dict[str, int]
    residual_entity_counts: dict[str, int]
    status: str


@dataclass(frozen=True)
class AnonymizationResult:
    """Anonymized text plus metadata safe to persist in an audit trail."""

    text: str
    audit: AnonymizationAudit


class OfflineEmailRecognizer(EmailRecognizer):
    """Use the bundled public suffix snapshot without network or writable caches."""

    _extract = TLDExtract(suffix_list_urls=(), cache_dir=None)

    def validate_result(self, pattern_text: str):
        return self._extract(pattern_text).fqdn != ""


def build_presidio_analyzer() -> AnalyzerEngine:
    """Build a bilingual Presidio analyzer with a French patient-reference recognizer.

    The required spaCy models must be installed locally. Missing models cause an
    exception instead of a silent pass-through, which is intentional.
    """

    provider = NlpEngineProvider(
        nlp_configuration={
            "nlp_engine_name": "spacy",
            "models": [
                {"lang_code": "fr", "model_name": "fr_core_news_md"},
                {"lang_code": "en", "model_name": "en_core_web_sm"},
            ],
        }
    )
    registry_recognizer = PatternRecognizer(
        supported_entity="PATIENT_REFERENCE",
        supported_language="fr",
        patterns=[
            Pattern(
                name="fr_patient_reference",
                regex=r"\b(?:patient|dossier)\s*(?:id|n°|numero|numéro)\s*[:#-]?\s*[A-Z0-9][A-Z0-9-]{3,}\b",
                score=0.85,
            )
        ],
    )
    analyzer = AnalyzerEngine(nlp_engine=provider.create_engine(), supported_languages=["fr", "en"])
    analyzer.registry.remove_recognizer("EmailRecognizer")
    for language in SUPPORTED_LANGUAGES:
        analyzer.registry.add_recognizer(OfflineEmailRecognizer(supported_language=language))
    analyzer.registry.add_recognizer(registry_recognizer)
    return analyzer


class TextAnonymizer:
    """Analyze, replace, and re-check PII without retaining source text in audit metadata."""

    def __init__(
        self,
        analyzer: Analyzer | None = None,
        anonymizer: Anonymizer | None = None,
        *,
        entities: Sequence[str] = PII_ENTITIES,
    ):
        unknown_entities = set(entities) - set(PII_ENTITIES)
        if not entities or unknown_entities:
            raise AnonymizationConfigurationError(
                f"Invalid PII entity policy: {sorted(unknown_entities)}."
            )
        self._analyzer = analyzer or build_presidio_analyzer()
        self._anonymizer = anonymizer or AnonymizerEngine()
        self._entities = tuple(entities)

    def anonymize(self, text: str, language: str) -> AnonymizationResult:
        """Return anonymized text or fail if detection/anonymization cannot complete safely."""

        if language not in SUPPORTED_LANGUAGES:
            raise AnonymizationConfigurationError(
                f"Unsupported language {language!r}; "
                f"supported languages are {sorted(SUPPORTED_LANGUAGES)}."
            )
        if not text.strip():
            raise ValueError("Text to anonymize must not be empty.")

        try:
            detections = self._analyzer.analyze(
                text=text, entities=self._entities, language=language
            )
            operators = {
                entity: OperatorConfig("replace", {"new_value": f"<{entity}>"})
                for entity in self._entities
            }
            output = self._anonymizer.anonymize(
                text=text,
                analyzer_results=detections,
                operators=operators,
            )
            residual = self._analyzer.analyze(
                text=output.text,
                entities=self._entities,
                language=language,
            )
        except Exception as exc:  # Presidio configuration and runtime errors must stop ingestion.
            raise AnonymizationConfigurationError(
                "PII anonymization could not complete safely."
            ) from exc

        detected_counts = _count_entities(detections)
        residual_counts = _count_entities(residual)
        status = "passed" if not residual_counts else "manual_review_required"
        return AnonymizationResult(
            text=output.text,
            audit=AnonymizationAudit(
                language=language,
                detected_entity_counts=detected_counts,
                residual_entity_counts=residual_counts,
                status=status,
            ),
        )


def _count_entities(results: Sequence[RecognizerResult]) -> dict[str, int]:
    return dict(sorted(Counter(result.entity_type for result in results).items()))
