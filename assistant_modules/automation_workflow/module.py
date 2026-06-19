from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List


@dataclass
class ChecklistItem:
    step: str
    done: bool = False


class AutomationWorkflowModule:
    """Automatización de guías, scripts e informes técnicos."""

    @staticmethod
    def create_checklist(steps: List[str]) -> List[ChecklistItem]:
        return [ChecklistItem(step=s, done=False) for s in steps]

    @staticmethod
    def script_template(task_name: str) -> str:
        return (
            f"#!/usr/bin/env bash\\n"
            f"# Script generado para: {task_name}\\n"
            "set -euo pipefail\\n"
            "echo 'Ejecutando tarea...'\\n"
        )

    @staticmethod
    def integration_status() -> dict:
        return {
            "github": "disponible vía herramientas remotas/API",
            "onedrive": "acceso por sistema de archivos local/sincronizado",
            "filesystem": "activo",
        }

    @staticmethod
    def generate_technical_report(output_dir: Path, title: str, sections: List[str]) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = output_dir / f"report_{ts}.md"
        body = [f"# {title}", "", f"Fecha: {datetime.now().isoformat()}", ""]
        for s in sections:
            body.extend([f"## {s}", "", "- Pendiente de completar", ""])
        path.write_text("\\n".join(body), encoding="utf-8")
        return path
