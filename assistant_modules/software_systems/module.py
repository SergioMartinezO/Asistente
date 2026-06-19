from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CodeSnippet:
    language: str
    code: str
    explanation: str


class SoftwareSystemsModule:
    """Generación/explicación base de software y estructuras."""

    def generate_code(self, language: str, task: str) -> CodeSnippet:
        lang = language.lower()
        if lang == "python":
            code = "def solve(data):\n    return sorted(data)"
        elif lang in ("c", "c++", "cpp"):
            code = "// TODO: implementar solución optimizada"
        elif lang == "java":
            code = "class Solution { /* TODO */ }"
        elif lang in ("js", "javascript"):
            code = "function solve(data){ return [...data].sort(); }"
        else:
            code = "// Lenguaje no soportado aún"
        return CodeSnippet(language=language, code=code, explanation=f"Plantilla inicial para: {task}")

    @staticmethod
    def big_o_hint(algorithm_name: str) -> str:
        return f"Analiza complejidad temporal y espacial de '{algorithm_name}' con mejor, promedio y peor caso."

    @staticmethod
    def uml_hint(system_name: str) -> str:
        return f"Diagrama UML sugerido para {system_name}: casos de uso + clases + secuencia."

    @staticmethod
    def design_patterns_hint(context: str) -> str:
        return f"Patrones candidatos para {context}: Strategy, Factory, Observer, Adapter."

    @staticmethod
    def ide_integration_status() -> dict:
        return {
            "vscode": "listo",
            "matlab": "disponible mediante actions/matlab_link.py",
            "simulink": "vía integración MATLAB",
        }
