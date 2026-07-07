from pathlib import Path

from core.output_policy import (
    normalize_tool_outputs,
    resolve_output_dir,
    resolve_output_file,
)


def test_resolve_output_file_forces_report_base(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("REX_REPORT_DIR", str(tmp_path))

    out1 = resolve_output_file(None, "a.txt")
    out2 = resolve_output_file("rel/b.txt", "x.txt")
    out3 = resolve_output_file(r"D:\otro\c.txt", "x.txt")

    assert Path(out1) == tmp_path / "a.txt"
    assert Path(out2) == tmp_path / "rel" / "b.txt"
    assert Path(out3) == tmp_path / "c.txt"


def test_normalize_tool_outputs_engineering_report(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("REX_REPORT_DIR", str(tmp_path))

    out = normalize_tool_outputs("engineering_report", {})

    assert Path(out["output_docx"]) == tmp_path / "Reporte_Proyecto.docx"
    assert Path(out["output_html"]) == tmp_path / "index.html"
    assert Path(out["diagram_dir"]) == tmp_path / "diagramas"


def test_resolve_output_dir_creates_folder(monkeypatch, tmp_path: Path):
    monkeypatch.setenv("REX_REPORT_DIR", str(tmp_path))
    out = Path(resolve_output_dir(None, "diagramas"))
    assert out.exists()
    assert out.is_dir()
