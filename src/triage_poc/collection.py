"""Track explicit intake answers without assigning clinical priority."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict

CollectionField = Literal[
    "age_group",
    "duration",
    "evolution",
    "intensity",
    "associated_symptoms",
    "medical_history",
    "allergies",
    "medications",
    "vulnerability_factors",
    "vitals",
]
AbsenceField = Literal[
    "associated_symptoms",
    "medical_history",
    "allergies",
    "medications",
    "vulnerability_factors",
]
COLLECTION_VERSION = "explicit-collection-v1-proposed"
QUESTIONS = {
    "age_group": ("Quelle est la tranche d'âge ?", "What is the age group?"),
    "duration": ("Depuis quand les symptômes sont-ils présents ?", "When did the symptoms start?"),
    "evolution": ("Comment les symptômes ont-ils évolué ?", "How have the symptoms changed?"),
    "intensity": (
        "Comment décririez-vous leur intensité ?",
        "How would you describe their severity?",
    ),
    "associated_symptoms": (
        "Quels autres symptômes sont présents, s'il y en a ?",
        "What other symptoms are present, if any?",
    ),
    "medical_history": (
        "Quels antécédents pertinents sont connus, s'il y en a ?",
        "What relevant medical history is known, if any?",
    ),
    "allergies": (
        "Quelles allergies sont connues, s'il y en a ?",
        "What allergies are known, if any?",
    ),
    "medications": (
        "Quels traitements sont pris actuellement, s'il y en a ?",
        "What medications are currently taken, if any?",
    ),
    "vulnerability_factors": (
        "Quels facteurs de vulnérabilité sont connus, s'il y en a ?",
        "What vulnerability factors are known, if any?",
    ),
    "vitals": (
        "Des constantes vitales mesurées sont-elles disponibles ?",
        "Are any measured vital signs available?",
    ),
}


class CollectionQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: CollectionField
    text: str


class CollectionProgress(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: str = COLLECTION_VERSION
    pending_fields: list[CollectionField]
    unavailable_fields: list[CollectionField]
    questions: list[CollectionQuestion]


def has_answer(context: dict, field: str) -> bool:
    value = context.get(field)
    if field == "age_group":
        return value not in (None, "unknown")
    if field == "vitals":
        return any(item is not None for item in (value or {}).values())
    return bool(value)


def validate_collection_status(context: dict) -> None:
    absent = context.get("confirmed_absent", [])
    unavailable = context.get("unavailable_fields", [])
    if len(set(absent)) != len(absent) or len(set(unavailable)) != len(unavailable):
        raise ValueError("Collection status fields must be unique.")
    if set(absent) & set(unavailable):
        raise ValueError("A field cannot be both absent and unavailable.")
    if any(has_answer(context, field) for field in [*absent, *unavailable]):
        raise ValueError("A supplied answer cannot also be absent or unavailable.")


def collection_progress(context: dict, language: str) -> CollectionProgress:
    """Return only unanswered fields; unknown is not a negative finding."""
    unavailable = context.get("unavailable_fields", [])
    settled = set(context.get("confirmed_absent", [])) | set(unavailable)
    pending = [
        field for field in QUESTIONS if field not in settled and not has_answer(context, field)
    ]
    return CollectionProgress(
        pending_fields=pending,
        unavailable_fields=[field for field in QUESTIONS if field in unavailable],
        questions=[
            CollectionQuestion(field=field, text=QUESTIONS[field][language == "en"])
            for field in pending[:2]
        ],
    )
