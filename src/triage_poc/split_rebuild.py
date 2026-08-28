"""Deterministically rebuild splits without normalized-question leakage."""

from __future__ import annotations

import hashlib
import re
import unicodedata


def normalized_question_key(question: str) -> str:
    text = unicodedata.normalize("NFKC", question).lower()
    return re.sub(r"\W+", "", text)


def assign_split(question: str) -> str:
    digest = hashlib.sha256(normalized_question_key(question).encode()).hexdigest()
    bucket = int(digest[:8], 16) % 100
    return "train" if bucket < 70 else "validation" if bucket < 85 else "test"
