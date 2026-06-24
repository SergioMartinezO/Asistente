from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import json


@dataclass(frozen=True)
class DiagramBundle:
    graphviz_png: Path
    graphviz_svg: Path
    mermaid_png: Path
    mermaid_svg: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "graphviz_png": self.graphviz_png,
            "graphviz_svg": self.graphviz_svg,
            "mermaid_png": self.mermaid_png,
            "mermaid_svg": self.mermaid_svg,
        }

    def existing_count(self) -> int:
        return sum(1 for p in self.as_dict().values() if p.exists())


def expected_bundle(diagram_dir: Path) -> DiagramBundle:
    return DiagramBundle(
        graphviz_png=diagram_dir / "diagrama_bloques_graphviz.png",
        graphviz_svg=diagram_dir / "diagrama_bloques_graphviz.svg",
        mermaid_png=diagram_dir / "diagrama_flujo_mermaid.png",
        mermaid_svg=diagram_dir / "diagrama_flujo_mermaid.svg",
    )


def write_manifest(diagram_dir: Path, bundle: DiagramBundle, project_title: str) -> Path:
    diagram_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "project_title": project_title,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "files": {
            key: {
                "path": str(path),
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
            for key, path in bundle.as_dict().items()
        },
    }
    manifest = diagram_dir / "manifest.json"
    manifest.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return manifest
