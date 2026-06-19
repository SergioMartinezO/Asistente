from __future__ import annotations

from dataclasses import dataclass
from typing import List
import re


@dataclass
class NLPResult:
    original_text: str
    normalized_text: str
    tokens: List[str]
    language: str = "es"


class SpanishNLPProcessor:
    """Procesamiento NLP básico orientado a español (rápido y sin dependencias pesadas)."""

    _token_re = re.compile(r"[a-zA-ZáéíóúÁÉÍÓÚñÑ0-9_]+")

    def normalize(self, text: str) -> str:
        return " ".join(text.strip().split()).lower()

    def tokenize(self, text: str) -> List[str]:
        return self._token_re.findall(text)

    def process(self, text: str) -> NLPResult:
        normalized = self.normalize(text)
        return NLPResult(
            original_text=text,
            normalized_text=normalized,
            tokens=self.tokenize(normalized),
        )
