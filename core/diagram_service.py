from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from datetime import datetime
import json


@dataclass(frozen=True)
class DiagramBundle:
    graphviz_png: Path
    graphviz_svg: Path
    circuit_png: Path
    circuit_svg: Path
    mermaid_png: Path
    mermaid_svg: Path
    power_png: Path
    power_svg: Path
    fsm_png: Path
    fsm_svg: Path
    sw_arch_png: Path
    sw_arch_svg: Path
    comm_png: Path
    comm_svg: Path
    mechanical_png: Path
    mechanical_svg: Path
    pcb_png: Path
    pcb_svg: Path
    uml_png: Path
    uml_svg: Path
    signal_flow_png: Path
    signal_flow_svg: Path

    def as_dict(self) -> dict[str, Path]:
        return {
            "graphviz_png": self.graphviz_png,
            "graphviz_svg": self.graphviz_svg,
            "circuit_png": self.circuit_png,
            "circuit_svg": self.circuit_svg,
            "mermaid_png": self.mermaid_png,
            "mermaid_svg": self.mermaid_svg,
            "power_png": self.power_png,
            "power_svg": self.power_svg,
            "fsm_png": self.fsm_png,
            "fsm_svg": self.fsm_svg,
            "sw_arch_png": self.sw_arch_png,
            "sw_arch_svg": self.sw_arch_svg,
            "comm_png": self.comm_png,
            "comm_svg": self.comm_svg,
            "mechanical_png": self.mechanical_png,
            "mechanical_svg": self.mechanical_svg,
            "pcb_png": self.pcb_png,
            "pcb_svg": self.pcb_svg,
            "uml_png": self.uml_png,
            "uml_svg": self.uml_svg,
            "signal_flow_png": self.signal_flow_png,
            "signal_flow_svg": self.signal_flow_svg,
        }

    def existing_count(self) -> int:
        return sum(1 for p in self.as_dict().values() if p.exists())


def expected_bundle(diagram_dir: Path) -> DiagramBundle:
    return DiagramBundle(
        graphviz_png=diagram_dir / "diagrama_bloques_graphviz.png",
        graphviz_svg=diagram_dir / "diagrama_bloques_graphviz.svg",
        circuit_png=diagram_dir / "diagrama_circuito_graphviz.png",
        circuit_svg=diagram_dir / "diagrama_circuito_graphviz.svg",
        mermaid_png=diagram_dir / "diagrama_flujo_mermaid.png",
        mermaid_svg=diagram_dir / "diagrama_flujo_mermaid.svg",
        power_png=diagram_dir / "diagrama_flujo_energia.png",
        power_svg=diagram_dir / "diagrama_flujo_energia.svg",
        fsm_png=diagram_dir / "diagrama_estados_fsm.png",
        fsm_svg=diagram_dir / "diagrama_estados_fsm.svg",
        sw_arch_png=diagram_dir / "diagrama_arquitectura_software.png",
        sw_arch_svg=diagram_dir / "diagrama_arquitectura_software.svg",
        comm_png=diagram_dir / "diagrama_comunicacion_hw_sw.png",
        comm_svg=diagram_dir / "diagrama_comunicacion_hw_sw.svg",
        mechanical_png=diagram_dir / "diagrama_mecanico.png",
        mechanical_svg=diagram_dir / "diagrama_mecanico.svg",
        pcb_png=diagram_dir / "boceto_pcb_layout.png",
        pcb_svg=diagram_dir / "boceto_pcb_layout.svg",
        uml_png=diagram_dir / "diagrama_uml.png",
        uml_svg=diagram_dir / "diagrama_uml.svg",
        signal_flow_png=diagram_dir / "diagrama_flujo_senal.png",
        signal_flow_svg=diagram_dir / "diagrama_flujo_senal.svg",
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