from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VisionRequest:
    prompt: str
    image_path: str


class MultimodalBridge:
    """Punto de extensión para visión (diagramas/esquemas) sin dependencia dura."""

    def analyze_diagram(self, request: VisionRequest) -> str:
        return (
            f"Análisis multimodal pendiente. Prompt='{request.prompt}', "
            f"imagen='{request.image_path}'."
        )
