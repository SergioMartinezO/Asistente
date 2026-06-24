from pathlib import Path
import json

from core.diagram_service import expected_bundle, write_manifest


def test_expected_bundle_paths(tmp_path: Path):
    bundle = expected_bundle(tmp_path)
    d = bundle.as_dict()
    assert d["graphviz_png"].name == "diagrama_bloques_graphviz.png"
    assert d["graphviz_svg"].name == "diagrama_bloques_graphviz.svg"
    assert d["mermaid_png"].name == "diagrama_flujo_mermaid.png"
    assert d["mermaid_svg"].name == "diagrama_flujo_mermaid.svg"


def test_write_manifest(tmp_path: Path):
    bundle = expected_bundle(tmp_path)
    # Simular archivos existentes
    bundle.graphviz_png.write_bytes(b"123")
    bundle.graphviz_svg.write_text("<svg></svg>", encoding="utf-8")

    manifest = write_manifest(tmp_path, bundle, "ProyectoTest")
    assert manifest.exists()

    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert data["project_title"] == "ProyectoTest"
    assert "files" in data
    assert data["files"]["graphviz_png"]["exists"] is True
    assert data["files"]["mermaid_png"]["exists"] is False
