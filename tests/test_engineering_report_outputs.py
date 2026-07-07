import base64
import json
import sys
import types
from pathlib import Path

import actions.engineering_report as er


_TINY_PNG_B64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5nX4sAAAAASUVORK5CYII="
)


def _write_tiny_png(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(_TINY_PNG_B64))


def _write_tiny_svg(path: Path, label: str = "diag"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        (
            "<svg xmlns='http://www.w3.org/2000/svg' width='200' height='80'>"
            "<rect x='0' y='0' width='200' height='80' fill='white' stroke='black'/>"
            f"<text x='10' y='45' font-size='14'>{label}</text>"
            "</svg>"
        ),
        encoding="utf-8",
    )


def _install_fake_docx(monkeypatch):
    class _Font:
        def __init__(self):
            self.name = None
            self.size = None
            self.bold = None
            self.color = types.SimpleNamespace(rgb=None)

    class _Run:
        def __init__(self, text=""):
            self.text = text
            self.bold = False
            self.font = _Font()

    class _Paragraph:
        def __init__(self, text=""):
            self.text = text
            self.runs = [_Run(text)] if text else []

        def add_run(self, text=""):
            r = _Run(text)
            self.runs.append(r)
            return r

    class _DummyTcPr(list):
        pass

    class _DummyTc:
        def __init__(self):
            self._tcpr = _DummyTcPr()

        def get_or_add_tcPr(self):
            return self._tcpr

    class _Cell:
        def __init__(self):
            self._text = ""
            self.paragraphs = [_Paragraph()]
            self._tc = _DummyTc()
            self.width = None

        @property
        def text(self):
            return self._text

        @text.setter
        def text(self, value):
            self._text = str(value)
            self.paragraphs = [_Paragraph(self._text)]

    class _Row:
        def __init__(self, cols: int):
            self.cells = [_Cell() for _ in range(cols)]

    class _Table:
        def __init__(self, rows: int, cols: int):
            self._cols = cols
            self.rows = [_Row(cols) for _ in range(rows)]
            self.style = None

        def add_row(self):
            row = _Row(self._cols)
            self.rows.append(row)
            return row

    class _FakeDocument:
        def __init__(self, *_args, **_kwargs):
            self.paragraphs = []

        def add_heading(self, text, level=1):
            p = _Paragraph(str(text))
            self.paragraphs.append(p)
            return p

        def add_paragraph(self, text=""):
            p = _Paragraph(str(text))
            self.paragraphs.append(p)
            return p

        def add_page_break(self):
            return None

        def add_table(self, rows: int, cols: int):
            return _Table(rows, cols)

        def add_picture(self, *_args, **_kwargs):
            return None

        def save(self, path):
            Path(path).parent.mkdir(parents=True, exist_ok=True)
            Path(path).write_bytes(b"FAKE-DOCX")

    fake_docx = types.ModuleType("docx")
    fake_docx.Document = _FakeDocument

    fake_shared = types.ModuleType("docx.shared")
    fake_shared.Inches = lambda x: float(x)

    class _Pt(float):
        pass

    class _RGBColor:
        def __init__(self, r, g, b):
            self.r = r
            self.g = g
            self.b = b

    fake_shared.Pt = _Pt
    fake_shared.RGBColor = _RGBColor

    fake_oxml = types.ModuleType("docx.oxml")

    class _DummyElement(dict):
        def set(self, k, v):
            self[k] = v

    fake_oxml.OxmlElement = lambda _name: _DummyElement()

    fake_oxml_ns = types.ModuleType("docx.oxml.ns")
    fake_oxml_ns.qn = lambda x: x

    monkeypatch.setitem(sys.modules, "docx", fake_docx)
    monkeypatch.setitem(sys.modules, "docx.shared", fake_shared)
    monkeypatch.setitem(sys.modules, "docx.oxml", fake_oxml)
    monkeypatch.setitem(sys.modules, "docx.oxml.ns", fake_oxml_ns)


def _patch_diagram_generators(monkeypatch):
    def _g(diagram_dir: Path, title: str):
        png = diagram_dir / "diagrama_bloques_graphviz.png"
        svg = diagram_dir / "diagrama_bloques_graphviz.svg"
        _write_tiny_png(png)
        _write_tiny_svg(svg, f"blocks:{title}")
        return {"png": png, "svg": svg}

    def _c(diagram_dir: Path, title: str):
        png = diagram_dir / "diagrama_circuito_graphviz.png"
        svg = diagram_dir / "diagrama_circuito_graphviz.svg"
        _write_tiny_png(png)
        _write_tiny_svg(svg, f"circuit:{title}")
        return {"png": png, "svg": svg}

    def _m(diagram_dir: Path, title: str, _code: str = ""):
        mmd = diagram_dir / "diagrama_flujo_mermaid.mmd"
        png = diagram_dir / "diagrama_flujo_mermaid.png"
        svg = diagram_dir / "diagrama_flujo_mermaid.svg"
        mmd.parent.mkdir(parents=True, exist_ok=True)
        mmd.write_text("flowchart TD; A-->B", encoding="utf-8")
        _write_tiny_png(png)
        _write_tiny_svg(svg, f"flow:{title}")
        return {"mmd": mmd, "png": png, "svg": svg}

    def _t(diagram_dir: Path, title: str, *_args, **_kwargs):
        png = diagram_dir / "grafica_pruebas_resultados.png"
        svg = diagram_dir / "grafica_pruebas_resultados.svg"
        _write_tiny_png(png)
        _write_tiny_svg(svg, f"tests:{title}")
        return {"png": png, "svg": svg}

    monkeypatch.setattr(er, "_generate_graphviz", _g)
    monkeypatch.setattr(er, "_generate_graphviz_circuit", _c)
    monkeypatch.setattr(er, "_generate_mermaid", _m)
    monkeypatch.setattr(er, "generate_test_results_chart", _t)


def test_engineering_report_generates_all_deliverables_and_device_diagrams(monkeypatch, tmp_path: Path):
    _install_fake_docx(monkeypatch)
    _patch_diagram_generators(monkeypatch)

    output_docx = tmp_path / "Reporte_Proyecto.docx"
    output_html = tmp_path / "index.html"
    diagram_dir = tmp_path / "diagramas"

    result = er.engineering_report(
        {
            "project_title": "Proyecto QA",
            "author": "QA",
            "institution": "UNAD",
            "version": "v2.0",
            "overview": "Prueba de entregables.",
            "template_path": str(tmp_path / "plantilla_inexistente.docx"),
            "output_docx": str(output_docx),
            "output_html": str(output_html),
            "diagram_dir": str(diagram_dir),
            "devices": ["ESP32", "Driver MOSFET"],
            "source_code": "print('ok')",
        },
        player=None,
        speak=None,
    )

    assert output_docx.exists(), "Debe generarse DOCX incluso sin plantilla"
    assert output_html.exists(), "Debe generarse HTML"

    # Bundle base + manifest base
    base_manifest = diagram_dir / "manifest.json"
    assert base_manifest.exists(), "Debe existir manifest base de diagramas"
    base_data = json.loads(base_manifest.read_text(encoding="utf-8"))
    assert "files" in base_data

    # Entregables críticos adicionales para Word/HTML
    assert (diagram_dir / "boceto_pcb_layout.png").exists(), "Debe existir PNG del boceto PCB para inserción en Word"
    assert (diagram_dir / "grafica_pruebas_resultados.png").exists(), "Debe existir gráfica de pruebas y resultados"

    html_text = output_html.read_text(encoding="utf-8")
    assert "Figura 6.1" in html_text, "El HTML debe incluir la gráfica de pruebas en la sección 6"
    assert "Informe Técnico Final" in html_text or "Consolidado" in html_text or "Conclusiones" in html_text

    # Bundles por dispositivo + manifest por dispositivo
    dev1 = diagram_dir / "ESP32"
    dev2 = diagram_dir / "Driver_MOSFET"
    for dev in (dev1, dev2):
        assert dev.exists(), f"Debe existir carpeta de dispositivo: {dev}"
        assert (dev / "manifest.json").exists(), f"Debe existir manifest en {dev}"
        assert (dev / "diagrama_bloques_graphviz.png").exists()
        assert (dev / "diagrama_circuito_graphviz.png").exists()
        assert (dev / "diagrama_flujo_mermaid.png").exists()

    assert "Dispositivos con diagramas: 2" in result


def test_engineering_report_keeps_html_when_word_fails(monkeypatch, tmp_path: Path):
    # Fuerza fallo en Word para validar que HTML no se pierde.
    monkeypatch.setitem(sys.modules, "docx", types.ModuleType("docx"))
    _patch_diagram_generators(monkeypatch)

    output_docx = tmp_path / "Reporte_Proyecto.docx"
    output_html = tmp_path / "index.html"
    diagram_dir = tmp_path / "diagramas"

    result = er.engineering_report(
        {
            "project_title": "Proyecto sin docx",
            "output_docx": str(output_docx),
            "output_html": str(output_html),
            "diagram_dir": str(diagram_dir),
            "source_code": "print('ok')",
        },
        player=None,
        speak=None,
    )

    assert output_html.exists(), "El HTML debe generarse aunque Word falle"
    assert "Word" in result and "FALLÓ" in result