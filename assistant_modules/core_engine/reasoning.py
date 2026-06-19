from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional


@dataclass
class ReasoningOutcome:
    intent: str
    confidence: float
    action: str
    metadata: Dict[str, Any]


class RexReasoningEngine:
    """Motor de reglas REX Protocol (ligero, explícito y auditable)."""

    def __init__(self) -> None:
        self._rules: Dict[str, Callable[[str], Optional[ReasoningOutcome]]] = {}
        self._register_default_rules()

    def _register_default_rules(self) -> None:
        def electronics_rule(text: str) -> Optional[ReasoningOutcome]:
            keys = ("resistencia", "ohm", "voltaje", "corriente", "circuito", "filtro")
            if any(k in text for k in keys):
                return ReasoningOutcome("electronics_query", 0.93, "electronics.solve", {"domain": "electronics"})
            return None

        def software_rule(text: str) -> Optional[ReasoningOutcome]:
            keys = ("python", "java", "c++", "algoritmo", "uml", "patrón")
            if any(k in text for k in keys):
                return ReasoningOutcome("software_query", 0.92, "software.solve", {"domain": "software"})
            return None

        def mechatronics_rule(text: str) -> Optional[ReasoningOutcome]:
            keys = ("torque", "servo", "arduino", "plc", "motor")
            if any(k in text for k in keys):
                return ReasoningOutcome("mechatronics_query", 0.9, "mechatronics.solve", {"domain": "mechatronics"})
            return None

        self._rules["electronics"] = electronics_rule
        self._rules["software"] = software_rule
        self._rules["mechatronics"] = mechatronics_rule

    def register_rule(self, name: str, handler: Callable[[str], Optional[ReasoningOutcome]]) -> None:
        self._rules[name] = handler

    def infer(self, normalized_text: str) -> ReasoningOutcome:
        for _, rule in self._rules.items():
            outcome = rule(normalized_text)
            if outcome is not None:
                return outcome
        return ReasoningOutcome("general_query", 0.7, "core.reply", {"domain": "general"})
