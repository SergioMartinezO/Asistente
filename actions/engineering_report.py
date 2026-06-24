from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
import html
import base64
from core.diagram_service import expected_bundle, write_manifest


def _log(player, message: str):
    if player and hasattr(player, "write_log"):
        player.write_log(message)


def _phase_start(player, phase: str, lines: List[str]):
    msg = f"[FASE] ▶ INICIO: {phase}"
    _log(player, msg)
    lines.append(msg)


def _phase_end(player, phase: str, lines: List[str]):
    msg = f"[FASE] ✅ FIN: {phase}"
    _log(player, msg)
    lines.append(msg)


def _safe_replace_placeholders(doc: Any, replacements: Dict[str, str]):
    for paragraph in doc.paragraphs:
        text = paragraph.text or ""
        new_text = text
        for key, value in replacements.items():
            new_text = new_text.replace(key, value)
        if new_text != text:
            paragraph.text = new_text


def _append_section(doc: Any, heading: str, body_lines: List[str]):
    _add_heading_safe(doc, heading, level=2)
    for line in body_lines:
        try:
            doc.add_paragraph(line, style="List Bullet")
        except Exception:
            doc.add_paragraph(f"• {line}")


def _append_code_section(doc: Any, heading: str, source_code: str):
    _add_heading_safe(doc, heading, level=2)
    p = doc.add_paragraph()
    run = p.add_run(source_code)
    run.font.name = "Consolas"


def _add_heading_safe(doc: Any, text: str, level: int = 1):
    """Inserta encabezado con fallback cuando la plantilla no tiene estilos Heading."""
    try:
        doc.add_heading(text, level=level)
        return
    except Exception:
        p = doc.add_paragraph(text)
        try:
            p.style = "Title" if level == 1 else "Subtitle"
        except Exception:
            pass


def _write_fallback_svg(svg_path: Path, title: str):
    svg_text = f"""<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='700'>
<rect x='0' y='0' width='1200' height='700' fill='#0f172a'/>
<rect x='40' y='40' width='1120' height='620' rx='14' fill='#111827' stroke='#334155' stroke-width='2'/>
<text x='70' y='120' fill='#93c5fd' font-size='40' font-family='Segoe UI'>Diagrama (fallback SVG)</text>
<text x='70' y='190' fill='#e2e8f0' font-size='28' font-family='Segoe UI'>{html.escape(title)}</text>
<text x='70' y='250' fill='#cbd5e1' font-size='24' font-family='Segoe UI'>No se pudo exportar el diagrama; se generó este SVG local.</text>
</svg>
"""
    svg_path.write_text(svg_text, encoding="utf-8")


def _write_fallback_png(png_path: Path, title: str):
    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (1200, 700), color=(15, 23, 42))
        draw = ImageDraw.Draw(img)
        draw.rectangle((40, 40, 1160, 660), outline=(51, 65, 85), width=3, fill=(17, 24, 39))
        draw.text((70, 90), "Diagrama (fallback PNG)", fill=(147, 197, 253))
        draw.text((70, 150), title, fill=(226, 232, 240))
        draw.text((70, 210), "No se pudo exportar Graphviz/Mermaid; generado localmente.", fill=(203, 213, 225))
        img.save(png_path)
    except Exception:
        # Último recurso sin Pillow: PNG 1x1 válido para evitar ausencia total de archivo.
        tiny_png_b64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5nX4sAAAAASUVORK5CYII="
        )
        try:
            png_path.write_bytes(base64.b64decode(tiny_png_b64))
        except Exception:
            pass


def _ensure_diagram_bundle(diagram_dir: Path, project_title: str) -> Dict[str, Path]:
    """Garantiza el bundle de 4 diagramas esperados (2 png + 2 svg)."""
    expected = expected_bundle(diagram_dir).as_dict()

    if not expected["graphviz_png"].exists():
        _write_fallback_png(expected["graphviz_png"], project_title)
    if not expected["graphviz_svg"].exists():
        _write_fallback_svg(expected["graphviz_svg"], project_title)
    if not expected["mermaid_png"].exists():
        _write_fallback_png(expected["mermaid_png"], project_title)
    if not expected["mermaid_svg"].exists():
        _write_fallback_svg(expected["mermaid_svg"], project_title)

    return expected


def _generate_graphviz(diagram_dir: Path, project_title: str) -> Dict[str, Optional[Path]]:
    graphviz_png = diagram_dir / "diagrama_bloques_graphviz.png"
    graphviz_svg = diagram_dir / "diagrama_bloques_graphviz.svg"
    legacy_stem = diagram_dir / "diagrama_bloques_graphviz"

    # Limpia artefacto heredado sin extensión generado por render() en versiones previas.
    try:
        if legacy_stem.exists() and legacy_stem.is_file():
            legacy_stem.unlink()
    except Exception:
        pass

    dot_source = """
digraph control_producto {
  rankdir=LR;
  graph [bgcolor="white", fontname="Segoe UI"];
  node  [shape=box, style="rounded,filled", fillcolor="#eaf6ff", color="#2f6f9f", fontname="Segoe UI"];
  edge  [color="#4d6b80", penwidth=1.4];

  I [label="Entradas/Sensores"];
  P [label="Procesamiento MCU"];
  A [label="Actuadores"];
  R [label="Retroalimentación"];

  I -> P;
  P -> A;
  A -> R;
  R -> P;
}
""".strip()

    def _render_local() -> bool:
        try:
            from graphviz import Source

            src = Source(dot_source)
            png_bytes = src.pipe(format="png")
            svg_bytes = src.pipe(format="svg")
            graphviz_png.write_bytes(png_bytes)
            graphviz_svg.write_bytes(svg_bytes)
            return graphviz_png.exists() and graphviz_svg.exists()
        except Exception:
            return False

    def _render_remote() -> bool:
        try:
            import requests

            ok = True
            for fmt, out_path in (("png", graphviz_png), ("svg", graphviz_svg)):
                url = f"https://kroki.io/graphviz/{fmt}"
                r = requests.post(
                    url,
                    data=dot_source.encode("utf-8"),
                    headers={"Content-Type": "text/plain; charset=utf-8"},
                    timeout=20,
                )
                if r.status_code == 200 and r.content:
                    out_path.write_bytes(r.content)
                else:
                    ok = False
            return ok and graphviz_png.exists() and graphviz_svg.exists()
        except Exception:
            return False

    if not _render_local() and not _render_remote():
        _write_fallback_png(graphviz_png, project_title)
        _write_fallback_svg(graphviz_svg, project_title)

    return {
        "png": graphviz_png if graphviz_png.exists() else None,
        "svg": graphviz_svg if graphviz_svg.exists() else None,
    }


def _generate_graphviz_circuit(diagram_dir: Path, project_title: str) -> Dict[str, Optional[Path]]:
    circuit_png = diagram_dir / "diagrama_circuito_graphviz.png"
    circuit_svg = diagram_dir / "diagrama_circuito_graphviz.svg"

    dot_source = """
digraph circuito_esquematico {
  rankdir=LR;
  graph [bgcolor="white", fontname="Segoe UI"];
  node  [shape=box, style="rounded,filled", fillcolor="#fff7ed", color="#c2410c", fontname="Segoe UI"];
  edge  [color="#9a3412", penwidth=1.4];

  PSU [label="Fuente 5V/3.3V"];
  MCU [label="ESP32 / MCU"];
  DHT [label="Sensor DHT22"];
  REL [label="Módulo Relé 4CH"];
  LOAD [label="Cargas externas"];
  GND [label="GND común"];

  PSU -> MCU [label="VCC"];
  PSU -> DHT [label="VCC"];
  PSU -> REL [label="VCC"];
  DHT -> MCU [label="DATA"];
  MCU -> REL [label="GPIO control"];
  REL -> LOAD [label="Conmutación"];
  MCU -> GND;
  DHT -> GND;
  REL -> GND;
}
""".strip()

    def _render_local() -> bool:
        try:
            from graphviz import Source

            src = Source(dot_source)
            png_bytes = src.pipe(format="png")
            svg_bytes = src.pipe(format="svg")
            circuit_png.write_bytes(png_bytes)
            circuit_svg.write_bytes(svg_bytes)
            return circuit_png.exists() and circuit_svg.exists()
        except Exception:
            return False

    def _render_remote() -> bool:
        try:
            import requests

            ok = True
            for fmt, out_path in (("png", circuit_png), ("svg", circuit_svg)):
                url = f"https://kroki.io/graphviz/{fmt}"
                r = requests.post(
                    url,
                    data=dot_source.encode("utf-8"),
                    headers={"Content-Type": "text/plain; charset=utf-8"},
                    timeout=20,
                )
                if r.status_code == 200 and r.content:
                    out_path.write_bytes(r.content)
                else:
                    ok = False
            return ok and circuit_png.exists() and circuit_svg.exists()
        except Exception:
            return False

    if not _render_local() and not _render_remote():
        _write_fallback_png(circuit_png, f"Circuito esquemático - {project_title}")
        _write_fallback_svg(circuit_svg, f"Circuito esquemático - {project_title}")

    return {
        "png": circuit_png if circuit_png.exists() else None,
        "svg": circuit_svg if circuit_svg.exists() else None,
    }


def _generate_mermaid(diagram_dir: Path, project_title: str) -> Dict[str, Optional[Path]]:
    mermaid_src = """
flowchart TD
    U[Usuario / Entorno] --> S[Sensores]
    S --> M[Microcontrolador]
    M --> D{Decisión de control}
    D -- Activar --> A[Actuador Principal]
    D -- Esperar --> E[Estado Seguro]
    A --> F[Realimentación]
    F --> M
""".strip()

    mmd_path = diagram_dir / "diagrama_flujo_mermaid.mmd"
    mermaid_png = diagram_dir / "diagrama_flujo_mermaid.png"
    mermaid_svg = diagram_dir / "diagrama_flujo_mermaid.svg"

    mmd_path.write_text(mermaid_src, encoding="utf-8")

    try:
        import requests

        for fmt, out_path in (("svg", mermaid_svg), ("png", mermaid_png)):
            url = f"https://kroki.io/mermaid/{fmt}"
            r = requests.post(
                url,
                data=mermaid_src.encode("utf-8"),
                headers={"Content-Type": "text/plain; charset=utf-8"},
                timeout=20,
            )
            if r.status_code == 200 and r.content:
                out_path.write_bytes(r.content)

    except Exception:
        pass

    if not mermaid_svg.exists():
        _write_fallback_svg(mermaid_svg, project_title)
    if not mermaid_png.exists():
        _write_fallback_png(mermaid_png, project_title)

    return {
        "mmd": mmd_path,
        "png": mermaid_png if mermaid_png.exists() else None,
        "svg": mermaid_svg if mermaid_svg.exists() else None,
    }


def _build_html(
    output_html: Path,
    project_title: str,
    overview: str,
    hardware_items: List[str],
    source_code: str,
    diagrams: List[Path],
    block_diagram: Optional[Path] = None,
    circuit_diagram: Optional[Path] = None,
):
    output_html.parent.mkdir(parents=True, exist_ok=True)

    hw = "\n".join(f"<li>{html.escape(item)}</li>" for item in hardware_items)
    gallery = []
    for p in diagrams:
        if not p.exists():
            continue
        try:
            rel = p.relative_to(output_html.parent).as_posix()
        except ValueError:
            # Fallback robusto cuando no comparten raíz (por ejemplo, distintas unidades).
            rel = p.resolve().as_uri()
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".svg", ".webp"}:
            gallery.append(
                f"<figure class='card'><img src='{html.escape(rel)}' alt='{html.escape(p.name)}' />"
                f"<figcaption>{html.escape(p.name)}</figcaption></figure>"
            )

    def _rel_or_uri(p: Optional[Path]) -> Optional[str]:
        if not p or not p.exists():
            return None
        try:
            return p.relative_to(output_html.parent).as_posix()
        except ValueError:
            return p.resolve().as_uri()

    block_src = _rel_or_uri(block_diagram)
    circuit_src = _rel_or_uri(circuit_diagram)

    sec31 = (
        f"<figure class='card'><img src='{html.escape(block_src)}' alt='Diagrama de bloques' />"
        f"<figcaption>Figura 3.1: Arquitectura de bloques funcionales del sistema.</figcaption></figure>"
        if block_src
        else "<p>No disponible: diagrama de bloques funcionales.</p>"
    )
    sec32 = (
        f"<figure class='card'><img src='{html.escape(circuit_src)}' alt='Diagrama de circuito' />"
        f"<figcaption>Figura 3.2: Circuito esquemático detallado de la solución de ingeniería.</figcaption></figure>"
        if circuit_src
        else "<p>No disponible: diagrama del circuito esquemático.</p>"
    )

    page = f"""<!doctype html>
<html lang='es'>
<head>
  <meta charset='utf-8' />
  <meta name='viewport' content='width=device-width,initial-scale=1' />
  <title>{html.escape(project_title)}</title>
  <style>
    body {{ font-family: Segoe UI, Arial, sans-serif; margin: 0; background: #0f172a; color: #e2e8f0; }}
    .wrap {{ max-width: 1100px; margin: 24px auto; padding: 0 16px; }}
    .card {{ background: #111827; border: 1px solid #334155; border-radius: 12px; padding: 14px; margin: 12px 0; }}
    h1, h2 {{ color: #93c5fd; }}
    pre {{ background: #020617; border: 1px solid #334155; border-radius: 8px; padding: 10px; overflow-x: auto; }}
    img {{ width: 100%; max-width: 900px; height: auto; border-radius: 10px; border: 1px solid #334155; }}
    .grid {{ display: grid; grid-template-columns: 1fr; gap: 12px; }}
    @media (min-width: 980px) {{ .grid {{ grid-template-columns: 1fr 1fr; }} }}
  </style>
</head>
<body>
  <div class='wrap'>
    <h1>{html.escape(project_title)}</h1>
    <section class='card'>
      <h2>Funcionamiento del producto</h2>
      <p>{html.escape(overview)}</p>
    </section>
    <section class='card'>
      <h2>Hardware</h2>
      <ul>{hw}</ul>
    </section>
    <section class='card'>
      <h2>Software</h2>
      <pre><code>{html.escape(source_code)}</code></pre>
    </section>
    <section class='card'>
      <h2>Diagramas</h2>
            <h3>3.1. Diagrama de Bloques Funcionales</h3>
            {sec31}
            <h3>3.2. Diagrama del Circuito Esquemático</h3>
            {sec32}
      <div class='grid'>{''.join(gallery) if gallery else '<p>Sin diagramas disponibles.</p>'}</div>
    </section>
  </div>
</body>
</html>
"""
    output_html.write_text(page, encoding="utf-8")


def engineering_report(parameters: Dict[str, Any], player=None, speak=None) -> str:
    """Genera reporte de ingeniería completo con plantilla Word + diagramas + página web."""
    lines: List[str] = []

    project_title = str(parameters.get("project_title") or "Proyecto Electrónico")
    author = str(parameters.get("author") or "Sergio Antonio Martinez Orozco")
    institution = str(parameters.get("institution") or "UNAD")
    overview = str(
        parameters.get("overview")
        or "Sistema de ingeniería con adquisición de datos, procesamiento y control de actuadores."
    )

    template_path = Path(str(parameters.get("template_path") or r"D:\IA\Asistente\templade\templade.docx"))
    output_docx = Path(str(parameters.get("output_docx") or r"D:\IA\Asistente\Report\Reporte_Proyecto.docx"))
    output_html = Path(str(parameters.get("output_html") or r"D:\IA\Asistente\Report\index.html"))
    diagram_dir = Path(str(parameters.get("diagram_dir") or r"D:\IA\Asistente\Report\diagramas"))

    hardware_items = parameters.get("hardware_items") or [
        "Microcontrolador principal con suficiente RAM/Flash para la lógica de control.",
        "Sensores de entrada con rango y precisión adecuados al entorno de operación.",
        "Etapa de potencia con protección y aislamiento para accionar cargas de forma segura.",
        "Fuente regulada y filtrada para estabilidad eléctrica y reducción de ruido.",
        "Conectores, protección ESD y fusibles para robustez en campo.",
    ]

    source_code = str(
        parameters.get("source_code")
        or (
            "// Código de referencia (Arduino)\n"
            "const int pinSensor = 34;\n"
            "const int pinActuador = 23;\n"
            "const float UMBRAL = 35.0;\n\n"
            "void setup(){\n"
            "  pinMode(pinActuador, OUTPUT);\n"
            "  Serial.begin(115200);\n"
            "}\n\n"
            "void loop(){\n"
            "  int lectura = analogRead(pinSensor);\n"
            "  float temp = (lectura / 4095.0) * 100.0; // Aproximación de ejemplo\n"
            "  if(temp > UMBRAL){\n"
            "    digitalWrite(pinActuador, HIGH); // Activa salida\n"
            "  } else {\n"
            "    digitalWrite(pinActuador, LOW);\n"
            "  }\n"
            "  delay(1000);\n"
            "}\n"
        )
    )

    try:
        try:
            from docx import Document
            from docx.shared import Inches
        except ModuleNotFoundError as dep_err:
            msg = (
                "Dependencia faltante para engineering_report: python-docx (módulo 'docx'). "
                "Instala el paquete 'python-docx' en el mismo Python que ejecuta main.py."
            )
            _log(player, f"❌ {msg}")
            return f"❌ {msg} Detalle: {dep_err}"

        # Fase 1: Hardware
        _phase_start(player, "Hardware", lines)
        _phase_end(player, "Hardware", lines)

        # Fase 2: Software
        _phase_start(player, "Software", lines)
        _phase_end(player, "Software", lines)

        # Fase 3: Diagramas
        _phase_start(player, "Diagramas", lines)
        diagram_dir.mkdir(parents=True, exist_ok=True)
        gv = _generate_graphviz(diagram_dir, project_title)
        gc = _generate_graphviz_circuit(diagram_dir, project_title)
        mm = _generate_mermaid(diagram_dir, project_title)
        expected = _ensure_diagram_bundle(diagram_dir, project_title)

        # Usar el estado real de archivos en disco para evitar perder inserciones
        # si alguna ruta intermedia retorna None pese a haberse generado el archivo.
        png_exts = {".png", ".jpg", ".jpeg", ".webp"}
        web_exts = png_exts | {".svg"}

        all_files = sorted([p for p in diagram_dir.iterdir() if p.is_file()])
        diagram_pngs = [
            expected["graphviz_png"],
            expected["mermaid_png"],
        ]
        diagram_web = [
            expected["graphviz_png"],
            expected["graphviz_svg"],
            gc.get("png") if gc.get("png") else diagram_dir / "diagrama_circuito_graphviz.png",
            gc.get("svg") if gc.get("svg") else diagram_dir / "diagrama_circuito_graphviz.svg",
            expected["mermaid_png"],
            expected["mermaid_svg"],
        ]

        if not diagram_pngs or not all(p.exists() for p in diagram_pngs):
            # Fallback adicional a rutas directas reportadas por generadores.
            diagram_pngs = [p for p in [gv.get("png"), mm.get("png")] if p and p.exists()] or [p for p in all_files if p.suffix.lower() in png_exts]
        if not diagram_web or not all(p.exists() for p in diagram_web):
            diagram_web = [p for p in [gv.get("png"), gv.get("svg"), mm.get("png"), mm.get("svg")] if p and p.exists()] or [p for p in all_files if p.suffix.lower() in web_exts]

        generated_count = sum(1 for p in expected.values() if p.exists())
        _log(player, f"ACT: Diagramas generados: {generated_count}/4")
        manifest = write_manifest(diagram_dir, expected_bundle(diagram_dir), project_title)
        _log(player, f"ACT: Manifest de diagramas: {manifest}")
        if hasattr(player, "update_activity"):
            try:
                player.update_activity(evento=f"Diagramas generados: {generated_count}/4")
            except Exception:
                pass

        _phase_end(player, "Diagramas", lines)

        # Fase 4: Word
        _phase_start(player, "Word", lines)
        if not template_path.exists():
            raise FileNotFoundError(
                f"No se encontró la plantilla: {template_path}. Verifica la ruta 'templade/templade.docx'."
            )

        doc = Document(str(template_path))
        today = datetime.now().strftime("%d/%m/%Y")
        _safe_replace_placeholders(
            doc,
            {
                "{{TITLE}}": project_title,
                "{{PROJECT_TITLE}}": project_title,
                "{{AUTHOR}}": author,
                "{{INSTITUTION}}": institution,
                "{{DATE}}": today,
            },
        )

        _add_heading_safe(doc, "Portada", level=1)
        doc.add_paragraph(project_title)
        doc.add_paragraph(f"Autor: {author}")
        doc.add_paragraph(f"Institución: {institution}")
        doc.add_paragraph(f"Fecha: {today}")

        _append_section(doc, "Hardware", [str(x) for x in hardware_items])
        _append_code_section(doc, "Software", source_code)
        _add_heading_safe(doc, "Diagramas", level=2)

        # Secciones solicitadas explícitamente por el usuario
        _add_heading_safe(doc, "3.1. Diagrama de Bloques Funcionales", level=3)
        doc.add_paragraph("Figura 3.1: Arquitectura de bloques funcionales del sistema.")
        block_png = expected["graphviz_png"] if expected["graphviz_png"].exists() else gv.get("png")
        if block_png and Path(block_png).exists():
            try:
                doc.add_picture(str(block_png), width=Inches(6.2))
            except Exception as pic_err:
                doc.add_paragraph(f"No se pudo insertar diagrama de bloques: {pic_err}")
        else:
            doc.add_paragraph("No disponible: diagrama de bloques funcionales.")

        _add_heading_safe(doc, "3.2. Diagrama del Circuito Esquemático", level=3)
        doc.add_paragraph("Figura 3.2: Circuito esquemático detallado de la solución de ingeniería.")
        circuit_png = gc.get("png") if gc.get("png") and Path(gc.get("png")).exists() else (diagram_dir / "diagrama_circuito_graphviz.png")
        if circuit_png and Path(circuit_png).exists():
            try:
                doc.add_picture(str(circuit_png), width=Inches(6.2))
            except Exception as pic_err:
                doc.add_paragraph(f"No se pudo insertar diagrama de circuito: {pic_err}")
        else:
            doc.add_paragraph("No disponible: diagrama del circuito esquemático.")

        inserted_word = 0
        # Contabilizar inserciones explícitas de 3.1 y 3.2
        if block_png and Path(block_png).exists():
            inserted_word += 1
        if circuit_png and Path(circuit_png).exists():
            inserted_word += 1
        for img in diagram_pngs:
            try:
                doc.add_paragraph(f"Diagrama insertado: {img.name}")
                doc.add_picture(str(img), width=Inches(6.2))
                inserted_word += 1
            except Exception as pic_err:
                doc.add_paragraph(f"No se pudo insertar {img.name}: {pic_err}")

        # Siempre documentar y enlazar también los SVG esperados en la sección Word.
        doc.add_paragraph("Diagramas SVG generados:")
        for svg in [expected["graphviz_svg"], expected["mermaid_svg"]]:
            if svg.exists():
                doc.add_paragraph(f"- {svg}")
            else:
                doc.add_paragraph(f"- SVG faltante: {svg.name}")

        output_docx.parent.mkdir(parents=True, exist_ok=True)
        doc.save(str(output_docx))
        _log(player, f"ACT: Diagramas insertados en Word: {inserted_word}/4")
        if hasattr(player, "update_activity"):
            try:
                player.update_activity(evento=f"Diagramas en Word: {inserted_word}/4")
            except Exception:
                pass
        _phase_end(player, "Word", lines)

        # Fase 5: Web
        _phase_start(player, "Web", lines)
        _build_html(
            output_html=output_html,
            project_title=project_title,
            overview=overview,
            hardware_items=[str(x) for x in hardware_items],
            source_code=source_code,
            diagrams=diagram_web,
            block_diagram=block_png if block_png and Path(block_png).exists() else None,
            circuit_diagram=circuit_png if circuit_png and Path(circuit_png).exists() else None,
        )
        inserted_web = sum(1 for p in diagram_web if p.exists() and p.suffix.lower() in web_exts)
        _log(player, f"ACT: Diagramas insertados en Web: {inserted_web}/6")
        if hasattr(player, "update_activity"):
            try:
                player.update_activity(evento=f"Diagramas en Web: {inserted_web}/6")
            except Exception:
                pass
        _phase_end(player, "Web", lines)

        final_msg = (
            "✅ Todas las actividades están completadas. "
            f"Word: {output_docx} | Web: {output_html}"
        )
        _log(player, final_msg)
        lines.append(final_msg)

        if speak:
            try:
                speak("Fases completadas. El reporte Word y la página web ya están listos.")
            except Exception:
                pass

        return "\n".join(lines)

    except Exception as e:
        err = f"❌ Error en engineering_report: {e}"
        _log(player, err)
        lines.append(err)
        return "\n".join(lines)
