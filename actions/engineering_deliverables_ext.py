# actions/engineering_deliverables_ext.py
"""
Extensión de entregables de ingeniería para el generador de reportes
(actions/engineering_report.py).

Este módulo completa la lista de entregables exigidos por la rúbrica de
proyectos de ingeniería (hardware, software e integrados) que el generador
original no producía:

  Hardware:
    - Diagrama de flujo de energía            -> generate_power_flow_diagram
    - Diagrama mecánico (vista 2D esquemática) -> generate_mechanical_diagram
    - Boceto de disposición de PCB             -> generate_pcb_layout_sketch
    - BOM (lista de materiales) formal         -> build_bom_rows / docx+html

  Software:
    - Diagrama de estados (FSM)                -> generate_fsm_diagram
    - Diagrama de arquitectura de software     -> generate_sw_architecture_diagram
    - Pseudocódigo de rutinas críticas         -> build_pseudocode

  Integrados:
    - Diagrama de comunicación HW-SW           -> generate_hw_sw_comm_diagram
    - Tabla de pruebas y resultados            -> build_test_results_rows
    - Manual de usuario / guía de operación    -> build_user_manual_sections

LIMITACIÓN HONESTA: un "PCB Layout" y un "diagrama mecánico" de nivel de
producción (ruteo de pistas real, modelo 3D del encapsulado) requieren una
herramienta EDA/CAD (KiCad, Altium, Proteus ARES, SolidWorks/Fusion 360) que
reciba el esquemático y la geometría real de los componentes. Este módulo no
sustituye esas herramientas: genera una representación esquemática/conceptual
2D (boceto de posición de componentes y trazas, croquis de encapsulado) útil
para el informe técnico, y dirige explícitamente al diseñador hacia el
archivo del esquemático (generado por `_generate_graphviz_circuit`) como
punto de partida para el ruteo real en una herramienta EDA.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional
import html


def _ensure_png_from_svg_or_placeholder(svg_path: Path, png_path: Path, label: str) -> None:
    """Garantiza un PNG para consumo en DOCX.

    Estrategia:
      1) Intentar convertir SVG→PNG con cairosvg.
      2) Si falla, dibujar PNG placeholder con Pillow.
      3) Si Pillow tampoco está, escribir PNG mínimo 1x1 válido.
    """
    # Regenera si no existe O si es el fallback m\u00ednimo de 1x1 px (< 500 bytes)
    if png_path.exists() and png_path.stat().st_size >= 500:
        return

    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=1280, output_height=800)
        if png_path.exists():
            return
    except Exception:
        pass

    try:
        from PIL import Image, ImageDraw

        img = Image.new("RGB", (1280, 800), color=(248, 250, 252))
        draw = ImageDraw.Draw(img)
        draw.rectangle((40, 40, 1240, 760), outline=(148, 163, 184), width=3, fill=(255, 255, 255))
        draw.text((80, 90), "Diagrama (fallback PNG)", fill=(30, 64, 175))
        draw.text((80, 150), label, fill=(51, 65, 85))
        img.save(png_path)
        if png_path.exists():
            return
    except Exception:
        pass

    try:
        import base64
        tiny = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO5nX4sAAAAASUVORK5CYII="
        png_path.write_bytes(base64.b64decode(tiny))
    except Exception:
        pass


# ── Render genérico Graphviz (local -> remoto -> fallback) ───────────────────
def render_graphviz(dot_source: str, png_path: Path, svg_path: Path,
                     fallback_label: str,
                     write_fallback_png=None, write_fallback_svg=None) -> Dict[str, Optional[Path]]:
    """Renderiza un DOT a PNG+SVG usando graphviz local, si no está disponible
    intenta el servicio remoto kroki.io, y si todo falla escribe un
    marcador visual (fallback) para que el entregable nunca quede vacío."""

    def _local() -> bool:
        try:
            from graphviz import Source
            src = Source(dot_source)
            png_path.write_bytes(src.pipe(format="png"))
            svg_path.write_bytes(src.pipe(format="svg"))
            return png_path.exists() and svg_path.exists()
        except Exception:
            return False

    def _remote() -> bool:
        try:
            import requests
            for fmt, out in (("png", png_path), ("svg", svg_path)):
                r = requests.post(f"https://kroki.io/graphviz/{fmt}",
                                   data=dot_source.encode("utf-8"),
                                   headers={"Content-Type": "text/plain; charset=utf-8"},
                                   timeout=25)
                if r.status_code == 200 and r.content:
                    out.write_bytes(r.content)
            return png_path.exists() and svg_path.exists()
        except Exception:
            return False

    if not _local() and not _remote():
        if write_fallback_png is not None:
            write_fallback_png(png_path, fallback_label)
        if write_fallback_svg is not None:
            write_fallback_svg(svg_path, fallback_label)

    return {"png": png_path if png_path.exists() else None,
            "svg": svg_path if svg_path.exists() else None}


# ── Diagrama de flujo de energía (Hardware) ───────────────────────────────────
def generate_power_flow_diagram(diagram_dir: Path, project_title: str,
                                 write_fallback_png=None, write_fallback_svg=None) -> Dict[str, Optional[Path]]:
    png = diagram_dir / "diagrama_flujo_energia.png"
    svg = diagram_dir / "diagrama_flujo_energia.svg"
    dot = r"""
digraph flujo_energia {
  rankdir=LR;
  graph [bgcolor="white", fontname="Helvetica", fontsize=13, pad="0.6", nodesep=0.6, ranksep=0.9,
         label="Diagrama de Flujo de Energía\nDistribución de la alimentación en el sistema",
         labelloc=t, labeljust=c];
  node [fontname="Helvetica", fontsize=11, margin="0.22,0.16", shape=box, style="filled,rounded"];
  edge [fontname="Helvetica", fontsize=9, penwidth=1.8];

  FUENTE [label="Fuente Primaria\n110/220 V AC o Batería 12 V DC", shape=parallelogram,
          fillcolor="#dcfce7", color="#16a34a"];
  PROT   [label="Protección\nFusible PTC 500 mA", shape=diamond, fillcolor="#fef9c3", color="#ca8a04"];
  REG5   [label="Regulador 5 V\n(hasta 2 A)", fillcolor="#bbf7d0", color="#15803d"];
  REG33  [label="Regulador 3.3 V\nAMS1117 (800 mA)", fillcolor="#bbf7d0", color="#15803d"];
  RAIL5  [label="Riel 5 V\n(actuadores, sensores 5 V)", fillcolor="#dbeafe", color="#2563eb"];
  RAIL33 [label="Riel 3.3 V\n(MCU, lógica digital)", fillcolor="#dbeafe", color="#2563eb"];
  MCU    [label="Microcontrolador", fillcolor="#e0e7ff", color="#4338ca"];
  SENS   [label="Sensores", fillcolor="#ffedd5", color="#c2410c"];
  ACT    [label="Actuadores / Potencia", fillcolor="#ede9fe", color="#7c3aed"];
  GND    [label="Plano de Tierra (GND)", shape=invtriangle, fillcolor="#f1f5f9", color="#475569"];

  FUENTE -> PROT   [label="V bruto"];
  PROT   -> REG5   [label="I protegida"];
  REG5   -> REG33  [label="5 V"];
  REG5   -> RAIL5  [label="5 V regulados"];
  REG33  -> RAIL33 [label="3.3 V regulados"];
  RAIL33 -> MCU    [label="alimenta"];
  RAIL5  -> SENS   [label="alimenta"];
  RAIL5  -> ACT    [label="alimenta (vía driver)"];
  MCU    -> GND [dir=none, style=dashed];
  SENS   -> GND [dir=none, style=dashed];
  ACT    -> GND [dir=none, style=dashed];
  REG5   -> GND [dir=none, style=dashed, label="referencia común"];
}
""".strip()
    return render_graphviz(dot, png, svg, f"Flujo de energía – {project_title}",
                            write_fallback_png, write_fallback_svg)


# ── Diagrama de estados FSM (Software) ────────────────────────────────────────
def generate_fsm_diagram(diagram_dir: Path, project_title: str,
                          write_fallback_png=None, write_fallback_svg=None) -> Dict[str, Optional[Path]]:
    png = diagram_dir / "diagrama_estados_fsm.png"
    svg = diagram_dir / "diagrama_estados_fsm.svg"
    dot = r"""
digraph fsm {
  rankdir=LR;
  graph [bgcolor="white", fontname="Helvetica", fontsize=13, pad="0.6",
         label="Diagrama de Estados (FSM)\nComportamiento del sistema según eventos",
         labelloc=t, labeljust=c];
  node [fontname="Helvetica", fontsize=11, shape=circle, style=filled, fillcolor="#dbeafe", color="#2563eb", fixedsize=false, width=1.1];
  edge [fontname="Helvetica", fontsize=9];

  INIT   [label="INICIALIZACIÓN", shape=doublecircle, fillcolor="#bbf7d0", color="#16a34a"];
  IDLE   [label="EN ESPERA\n(IDLE)"];
  LECT   [label="LECTURA\nDE SENSOR"];
  EVAL   [label="EVALUACIÓN\nDE UMBRAL", shape=diamond, fillcolor="#fef9c3", color="#ca8a04"];
  ACTIVO [label="ACTUADOR\nACTIVO", fillcolor="#ede9fe", color="#7c3aed"];
  ERROR  [label="ERROR /\nFALLA", fillcolor="#fecaca", color="#dc2626"];
  APAGA  [label="APAGADO\nSEGURO", shape=doublecircle, fillcolor="#e2e8f0", color="#475569"];

  INIT   -> IDLE   [label="setup() OK"];
  IDLE   -> LECT   [label="tick del temporizador"];
  LECT   -> EVAL   [label="dato adquirido"];
  EVAL   -> ACTIVO [label="valor ≥ umbral alto"];
  EVAL   -> IDLE   [label="valor ≤ umbral bajo"];
  ACTIVO -> IDLE   [label="condición de apagado"];
  LECT   -> ERROR  [label="excepción / timeout"];
  ERROR  -> IDLE   [label="reintento OK"];
  ERROR  -> APAGA  [label="fallo crítico"];
  IDLE   -> APAGA  [label="interrupción del usuario"];
}
""".strip()
    return render_graphviz(dot, png, svg, f"FSM – {project_title}",
                            write_fallback_png, write_fallback_svg)


# ── Diagrama de arquitectura de software (Software) ───────────────────────────
def generate_sw_architecture_diagram(diagram_dir: Path, project_title: str,
                                      write_fallback_png=None, write_fallback_svg=None) -> Dict[str, Optional[Path]]:
    png = diagram_dir / "diagrama_arquitectura_software.png"
    svg = diagram_dir / "diagrama_arquitectura_software.svg"
    dot = r"""
digraph arquitectura_sw {
  rankdir=TB;
  graph [bgcolor="white", fontname="Helvetica", fontsize=13, pad="0.6", ranksep=0.7,
         label="Diagrama de Arquitectura de Software\nCapas, módulos y comunicación",
         labelloc=t, labeljust=c];
  node [fontname="Helvetica", fontsize=11, shape=box, style="filled,rounded"];
  edge [fontname="Helvetica", fontsize=9];

  subgraph cluster_ui {
    label="Capa de Presentación"; style="filled,rounded"; color="#2563eb"; fillcolor="#eff6ff";
    UI [label="Interfaz de usuario /\nConsola de estado"];
  }
  subgraph cluster_logic {
    label="Capa de Lógica de Control"; style="filled,rounded"; color="#7c3aed"; fillcolor="#f5f3ff";
    CTRL [label="Máquina de estados\n(control principal)"];
    RULES [label="Reglas de decisión\n(umbrales / histéresis)"];
  }
  subgraph cluster_hal {
    label="Capa de Abstracción de Hardware (HAL)"; style="filled,rounded"; color="#ea580c"; fillcolor="#fff7ed";
    SENSOR_DRV [label="Driver de sensor\n(ADC / I2C / SPI)"];
    ACT_DRV    [label="Driver de actuador\n(PWM / GPIO)"];
  }
  subgraph cluster_infra {
    label="Capa de Infraestructura"; style="filled,rounded"; color="#16a34a"; fillcolor="#f0fdf4";
    LOG [label="Registro de eventos\n(logging)"];
    COMM [label="Comunicación\n(UART / Wi-Fi / MQTT)"];
  }

  UI -> CTRL [label="comandos / eventos"];
  CTRL -> RULES [label="consulta"];
  CTRL -> SENSOR_DRV [label="lee"];
  CTRL -> ACT_DRV [label="escribe"];
  CTRL -> LOG [label="registra"];
  CTRL -> COMM [label="publica telemetría"];
  SENSOR_DRV -> RULES [label="dato crudo"];
}
""".strip()
    return render_graphviz(dot, png, svg, f"Arquitectura SW – {project_title}",
                            write_fallback_png, write_fallback_svg)


# ── Diagrama de comunicación HW-SW (Integrado) ────────────────────────────────
def generate_hw_sw_comm_diagram(diagram_dir: Path, project_title: str,
                                 write_fallback_png=None, write_fallback_svg=None) -> Dict[str, Optional[Path]]:
    png = diagram_dir / "diagrama_comunicacion_hw_sw.png"
    svg = diagram_dir / "diagrama_comunicacion_hw_sw.svg"
    dot = r"""
digraph comunicacion_hw_sw {
  rankdir=LR;
  graph [bgcolor="white", fontname="Helvetica", fontsize=13, pad="0.6",
         label="Diagrama de Comunicación Hardware-Software\nInteracción entre sensores, microcontrolador y programa",
         labelloc=t, labeljust=c];
  node [fontname="Helvetica", fontsize=11, shape=box, style="filled,rounded"];
  edge [fontname="Helvetica", fontsize=9];

  SENS [label="Sensor físico\n(magnitud analógica/digital)", fillcolor="#ffedd5", color="#c2410c"];
  ADC  [label="ADC / Interfaz digital\n(hardware del MCU)", fillcolor="#dbeafe", color="#2563eb"];
  DRV  [label="Driver / HAL\n(software)", fillcolor="#f5f3ff", color="#7c3aed"];
  APP  [label="Lógica de aplicación\n(software de control)", fillcolor="#f5f3ff", color="#7c3aed"];
  OUT  [label="Salida digital / PWM\n(hardware del MCU)", fillcolor="#dbeafe", color="#2563eb"];
  ACT  [label="Actuador físico", fillcolor="#ede9fe", color="#6d28d9"];
  UI   [label="Usuario / Nube\n(monitoreo)", fillcolor="#ecfeff", color="#0891b2"];

  SENS -> ADC [label="señal eléctrica"];
  ADC  -> DRV [label="registro / interrupción"];
  DRV  -> APP [label="valor procesado (API)"];
  APP  -> DRV [label="comando de actuación"];
  DRV  -> OUT [label="escritura de registro"];
  OUT  -> ACT [label="señal de potencia"];
  APP  -> UI  [label="telemetría / logs"];
  UI   -> APP [label="configuración remota", style=dashed];
}
""".strip()
    return render_graphviz(dot, png, svg, f"Comunicación HW-SW – {project_title}",
                            write_fallback_png, write_fallback_svg)


# ── Diagrama mecánico (Hardware, vista 2D esquemática) ────────────────────────
def generate_mechanical_diagram(diagram_dir: Path, project_title: str,
                                 write_fallback_png=None, write_fallback_svg=None) -> Dict[str, Optional[Path]]:
    """
    Genera una vista 2D esquemática (croquis acotado) del encapsulado/caja
    del proyecto. NOTA: no reemplaza un modelo CAD 2D/3D real (SolidWorks,
    Fusion 360, FreeCAD); sirve como referencia conceptual de disposición
    física para el informe técnico.
    """
    png = diagram_dir / "diagrama_mecanico.png"
    svg = diagram_dir / "diagrama_mecanico.svg"
    dot = r"""
graph mecanico {
  layout=neato;
  graph [bgcolor="white", fontname="Helvetica", fontsize=12,
         label="Diagrama Mecánico — Croquis 2D del Encapsulado (vista superior)\nCotas orientativas en mm — referencia conceptual, no sustituye plano CAD",
         labelloc=b, labeljust=c];
  node [fontname="Helvetica", fontsize=9, shape=box, style="filled,rounded"];

  ENC [label="Caja / Chasis\n120 x 80 x 40 mm", pos="0,0!", width=3.0, height=2.0,
       fixedsize=true, fillcolor="#f1f5f9", color="#334155", penwidth=2];
  PCB [label="PCB principal\n100 x 60 mm", pos="0,0.1!", width=2.4, height=1.4,
       fixedsize=true, fillcolor="#dbeafe", color="#2563eb"];
  CONN1 [label="Conector\nalimentación", pos="-1.7,0.9!", width=0.9, height=0.4,
         fixedsize=true, fillcolor="#dcfce7", color="#16a34a", fontsize=8];
  CONN2 [label="Puerto\nUSB/UART", pos="1.7,0.9!", width=0.9, height=0.4,
         fixedsize=true, fillcolor="#cffafe", color="#0891b2", fontsize=8];
  VENT [label="Rejillas de\nventilación", pos="0,-1.1!", width=1.4, height=0.35,
        fixedsize=true, fillcolor="#fef9c3", color="#ca8a04", fontsize=8];
  MOUNT1 [label="Ø3", pos="-1.5,1.0!", width=0.4, height=0.4, shape=circle,
          fixedsize=true, fillcolor="#e2e8f0", color="#475569", fontsize=7];
  MOUNT2 [label="Ø3", pos="1.5,1.0!", width=0.4, height=0.4, shape=circle,
          fixedsize=true, fillcolor="#e2e8f0", color="#475569", fontsize=7];
  MOUNT3 [label="Ø3", pos="-1.5,-1.0!", width=0.4, height=0.4, shape=circle,
          fixedsize=true, fillcolor="#e2e8f0", color="#475569", fontsize=7];
  MOUNT4 [label="Ø3", pos="1.5,-1.0!", width=0.4, height=0.4, shape=circle,
          fixedsize=true, fillcolor="#e2e8f0", color="#475569", fontsize=7];
}
""".strip()
    return render_graphviz(dot, png, svg, f"Diagrama mecánico – {project_title}",
                            write_fallback_png, write_fallback_svg)


# ── Boceto de disposición de PCB (Hardware, conceptual) ───────────────────────
def generate_pcb_layout_sketch(diagram_dir: Path, project_title: str,
                                components: Optional[List[Dict[str, str]]] = None) -> Dict[str, Optional[Path]]:
    """
    Genera un boceto SVG de disposición de componentes tipo PCB (footprint
    aproximado + rutas rectilíneas simplificadas). No es un ruteo real:
    para producción, el esquemático generado (diagrama_circuito_graphviz)
    debe importarse a una herramienta EDA (KiCad, Proteus ARES, Altium)
    donde se realice el ruteo de pistas y la verificación DRC.
    """
    diagram_dir.mkdir(parents=True, exist_ok=True)
    svg_path = diagram_dir / "boceto_pcb_layout.svg"
    png_path = diagram_dir / "boceto_pcb_layout.png"

    comps = components or []
    names = [c.get("nombre", f"U{i+1}") for i, c in enumerate(comps)][:8]
    if not names:
        names = ["MCU", "REG 3V3", "SENSOR", "MOSFET", "OPTO", "CONN PWR", "CONN USB", "LED"]

    # Distribuye "footprints" en una rejilla simple sobre un área de PCB.
    board_w, board_h = 640, 420
    margin = 40
    cols = 4
    cell_w = (board_w - 2 * margin) // cols
    rows = (len(names) + cols - 1) // cols
    cell_h = (board_h - 2 * margin) // max(rows, 1)

    footprints = []
    centers = []
    for i, name in enumerate(names):
        r, c = divmod(i, cols)
        x = margin + c * cell_w + 10
        y = margin + r * cell_h + 10
        w = cell_w - 20
        h = cell_h - 20
        cx, cy = x + w / 2, y + h / 2
        centers.append((cx, cy))
        footprints.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="4" '
            f'fill="#fde68a" stroke="#92400e" stroke-width="1.5"/>'
            f'<text x="{cx}" y="{cy}" font-size="11" text-anchor="middle" '
            f'dominant-baseline="middle" font-family="Helvetica">{html.escape(str(name))[:16]}</text>'
        )

    # Trazas simplificadas: conecta cada footprint con el siguiente (bus lineal).
    traces = []
    for i in range(len(centers) - 1):
        x1, y1 = centers[i]
        x2, y2 = centers[i + 1]
        traces.append(
            f'<path d="M{x1},{y1} L{x1},{(y1+y2)/2} L{x2},{(y1+y2)/2} L{x2},{y2}" '
            f'fill="none" stroke="#b45309" stroke-width="2"/>'
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {board_w} {board_h+60}" font-family="Helvetica">
  <rect x="0" y="0" width="{board_w}" height="{board_h+60}" fill="white"/>
  <text x="{board_w/2}" y="24" font-size="15" font-weight="bold" text-anchor="middle">
    Boceto de Disposición de PCB — {html.escape(project_title)}
  </text>
  <rect x="10" y="40" width="{board_w-20}" height="{board_h-20}" rx="6"
        fill="#166534" fill-opacity="0.08" stroke="#166534" stroke-width="2"/>
  {''.join(footprints)}
  {''.join(traces)}
  <text x="{board_w/2}" y="{board_h+40}" font-size="10" fill="#64748b" text-anchor="middle">
    Croquis conceptual de posición de componentes y trazas — NO apto para fabricación.
    Ruteo real debe hacerse en KiCad / Proteus ARES a partir del esquemático.
  </text>
</svg>"""
    svg_path.write_text(svg, encoding="utf-8")

    # Para Word se necesita PNG: garantizar artefacto aunque falten dependencias.
    _ensure_png_from_svg_or_placeholder(svg_path, png_path, f"PCB layout conceptual – {project_title}")

    return {"svg": svg_path if svg_path.exists() else None,
            "png": png_path if png_path.exists() else None}


def generate_test_results_chart(diagram_dir: Path, project_title: str,
                                write_fallback_png=None, write_fallback_svg=None) -> Dict[str, Optional[Path]]:
    """Genera una gráfica simple de resultados de validación (aprobadas/pendientes).

    Esta gráfica cumple el requisito de 'mediciones y gráficas' como apoyo visual.
    """
    png = diagram_dir / "grafica_pruebas_resultados.png"
    svg = diagram_dir / "grafica_pruebas_resultados.svg"

    dot = r"""
digraph grafica_pruebas {
  rankdir=LR;
  graph [bgcolor="white", fontname="Helvetica", fontsize=12,
         label="Gráfica de Pruebas y Resultados\nEstado de validación del sistema",
         labelloc=t, labeljust=c, pad="0.5"];
  node [shape=box, style="filled,rounded", fontname="Helvetica", fontsize=10];
  edge [color="#64748b"];

  A [label="Pruebas planeadas\n6", fillcolor="#e2e8f0", color="#475569"];
  B [label="Aprobadas\n0", fillcolor="#bbf7d0", color="#15803d"];
  C [label="Pendientes\n6", fillcolor="#fde68a", color="#92400e"];
  D [label="Con fallo\n0", fillcolor="#fecaca", color="#dc2626"];

  A -> B;
  A -> C;
  A -> D;
}
""".strip()

    return render_graphviz(dot, png, svg, f"Gráfica de pruebas – {project_title}",
                           write_fallback_png, write_fallback_svg)


# ── BOM (lista de materiales formal) ──────────────────────────────────────────
def build_bom_rows(components: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Normaliza la lista de componentes a filas de BOM con referencia,
    cantidad, descripción y especificación (los campos que exige un BOM
    formal, además de la justificación técnica ya presente)."""
    rows = []
    for i, c in enumerate(components):
        ref = c.get("referencia") or f"U{i+1}" if "microcontrolador" in c.get("nombre", "").lower() else c.get("referencia")
        if not ref:
            ref = f"C{i+1}"
        rows.append({
            "ref": str(c.get("referencia") or ref),
            "cantidad": str(c.get("cantidad") or "1"),
            "descripcion": c.get("nombre", ""),
            "especificacion": c.get("especificacion", ""),
        })
    return rows


def build_bom_docx_table(doc, components: List[Dict[str, str]]):
    rows = build_bom_rows(components)
    table = doc.add_table(rows=1, cols=4)
    try:
        table.style = "Light Grid Accent 1"
    except Exception:
        pass
    hdr = table.rows[0].cells
    for cell, text in zip(hdr, ["Ref.", "Cant.", "Descripción", "Especificación técnica"]):
        cell.text = text
    for r in rows:
        cells = table.add_row().cells
        cells[0].text = r["ref"]
        cells[1].text = r["cantidad"]
        cells[2].text = r["descripcion"]
        cells[3].text = r["especificacion"]
    return table


def build_bom_table_html(components: List[Dict[str, str]]) -> str:
    rows = build_bom_rows(components)
    body = "".join(
        f"<tr><td>{html.escape(r['ref'])}</td><td>{html.escape(r['cantidad'])}</td>"
        f"<td>{html.escape(r['descripcion'])}</td><td>{html.escape(r['especificacion'])}</td></tr>"
        for r in rows
    )
    return (
        "<table class='comp-table'><thead><tr>"
        "<th>Ref.</th><th>Cant.</th><th>Descripción</th><th>Especificación técnica</th>"
        f"</tr></thead><tbody>{body}</tbody></table>"
    )


# ── Pseudocódigo de rutinas críticas (Software) ───────────────────────────────
def build_pseudocode(project_title: str) -> str:
    return (
        "INICIO\n"
        "  Configurar pines de sensor (entrada) y actuador (salida)\n"
        "  Establecer UMBRAL_ALTO, UMBRAL_BAJO, PERIODO_MUESTREO\n"
        "  estado_actuador <- FALSO\n\n"
        "  MIENTRAS sistema encendido HACER\n"
        "    lectura <- LEER_SENSOR(pin_sensor)\n"
        "    valor_pct <- ESCALAR(lectura, 0, RESOLUCION_ADC, 0, 100)\n\n"
        "    SI valor_pct >= UMBRAL_ALTO Y estado_actuador = FALSO ENTONCES\n"
        "      ACTIVAR_ACTUADOR(pin_actuador)\n"
        "      estado_actuador <- VERDADERO\n"
        "      REGISTRAR_EVENTO(\"activación\", valor_pct)\n"
        "    SINO SI valor_pct <= UMBRAL_BAJO Y estado_actuador = VERDADERO ENTONCES\n"
        "      DESACTIVAR_ACTUADOR(pin_actuador)\n"
        "      estado_actuador <- FALSO\n"
        "      REGISTRAR_EVENTO(\"desactivación\", valor_pct)\n"
        "    FIN SI\n\n"
        "    SI ocurre_excepcion ENTONCES\n"
        "      REGISTRAR_EVENTO(\"error\", detalle_excepcion)\n"
        "      ESPERAR(2 s)  // reintento controlado\n"
        "    FIN SI\n\n"
        "    ESPERAR(PERIODO_MUESTREO)\n"
        "  FIN MIENTRAS\n\n"
        "  // Rutina de apagado seguro\n"
        "  DESACTIVAR_ACTUADOR(pin_actuador)\n"
        "FIN\n"
    )


# ── Tabla de pruebas y resultados (Integrado) ─────────────────────────────────
def build_test_results_rows(project_title: str) -> List[Dict[str, str]]:
    return [
        {"prueba": "Alimentación",
         "condicion": "Medir tensión en riel 3.3 V y 5 V con multímetro",
         "esperado": "3.3 V ± 3% / 5 V ± 3%",
         "obtenido": "Pendiente de medición en banco de pruebas",
         "estado": "Pendiente"},
        {"prueba": "Lectura de sensor",
         "condicion": "Aplicar entrada conocida y leer valor ADC",
         "esperado": "Error < 2% del fondo de escala",
         "obtenido": "Pendiente de medición en banco de pruebas",
         "estado": "Pendiente"},
        {"prueba": "Activación del actuador",
         "condicion": "Forzar valor por encima del umbral alto",
         "esperado": "Actuador conmuta en < 500 ms",
         "obtenido": "Pendiente de medición en banco de pruebas",
         "estado": "Pendiente"},
        {"prueba": "Histéresis de control",
         "condicion": "Ciclar valor entre umbral alto y bajo",
         "esperado": "Sin oscilación (chattering) del actuador",
         "obtenido": "Pendiente de medición en banco de pruebas",
         "estado": "Pendiente"},
        {"prueba": "Comunicación / telemetría",
         "condicion": "Verificar publicación de datos por UART o Wi-Fi",
         "esperado": "Paquete recibido cada período de muestreo, sin pérdidas > 1%",
         "obtenido": "Pendiente de medición en banco de pruebas",
         "estado": "Pendiente"},
        {"prueba": "Recuperación ante error",
         "condicion": "Desconectar sensor en caliente",
         "esperado": "Sistema registra error y reintenta sin bloquearse",
         "obtenido": "Pendiente de medición en banco de pruebas",
         "estado": "Pendiente"},
    ]


def build_test_results_docx_table(doc, project_title: str):
    rows = build_test_results_rows(project_title)
    table = doc.add_table(rows=1, cols=5)
    try:
        table.style = "Light Grid Accent 1"
    except Exception:
        pass
    hdr = table.rows[0].cells
    for cell, text in zip(hdr, ["Prueba", "Condición", "Resultado esperado", "Resultado obtenido", "Estado"]):
        cell.text = text
    for r in rows:
        cells = table.add_row().cells
        cells[0].text = r["prueba"]
        cells[1].text = r["condicion"]
        cells[2].text = r["esperado"]
        cells[3].text = r["obtenido"]
        cells[4].text = r["estado"]
    return table


def build_test_results_table_html(project_title: str) -> str:
    rows = build_test_results_rows(project_title)
    body = "".join(
        f"<tr><td>{html.escape(r['prueba'])}</td><td>{html.escape(r['condicion'])}</td>"
        f"<td>{html.escape(r['esperado'])}</td><td>{html.escape(r['obtenido'])}</td>"
        f"<td>{html.escape(r['estado'])}</td></tr>"
        for r in rows
    )
    return (
        "<table class='comp-table'><thead><tr>"
        "<th>Prueba</th><th>Condición</th><th>Resultado esperado</th>"
        "<th>Resultado obtenido</th><th>Estado</th>"
        f"</tr></thead><tbody>{body}</tbody></table>"
    )


# ── Manual de usuario / guía de operación (Software/Integrado) ───────────────
def build_user_manual_sections(project_title: str, overview: str, device_names: List[str]) -> List[str]:
    devices_txt = ", ".join(device_names) if device_names else project_title
    return [
        "1. Descripción general: " + overview,
        f"2. Dispositivos/módulos cubiertos: {devices_txt}.",
        "3. Requisitos previos: fuente de alimentación regulada, cableado según "
        "el diagrama esquemático, firmware cargado (main_control.py) en el "
        "microcontrolador.",
        "4. Encendido: conectar la alimentación; el LED indicador confirma "
        "inicialización correcta (ver Diagrama de Estados, estado INICIALIZACIÓN).",
        "5. Operación normal: el sistema adquiere la señal del sensor de forma "
        "periódica y activa el actuador automáticamente al superar el umbral "
        "configurado (ver sección de Lógica de Control).",
        "6. Indicadores de estado: LED apagado = en espera; LED encendido = "
        "actuador activo; parpadeo = condición de error (ver tabla de Pruebas y Resultados).",
        "7. Apagado seguro: desconectar la alimentación únicamente cuando el "
        "actuador esté en estado 'apagado' para evitar transitorios en la carga.",
        "8. Mantenimiento: verificar periódicamente las conexiones y limpiar "
        "el sensor según la hoja de datos del componente.",
        "9. Solución de problemas: si el sistema no responde, revisar la "
        "sección 'Pruebas y Resultados' del informe técnico y los registros "
        "(log) generados por el software.",
    ]


def build_user_manual_html(project_title: str, overview: str, device_names: List[str]) -> str:
    items = build_user_manual_sections(project_title, overview, device_names)
    return "<ol>" + "".join(f"<li>{html.escape(i)}</li>" for i in items) + "</ol>"


# ── Diagrama UML (clases, casos de uso, secuencia) ─────────────────────────────
def generate_uml_diagram(diagram_dir: Path, project_title: str,
                         write_fallback_png=None, write_fallback_svg=None) -> Dict[str, Optional[Path]]:
    png = diagram_dir / "diagrama_uml.png"
    svg = diagram_dir / "diagrama_uml.svg"
    dot = r"""
digraph uml_diagrams {
  rankdir=TB;
  graph [bgcolor="white", fontname="Helvetica", fontsize=12, pad="0.5",
         label="Diagramas UML (Clases y Casos de Uso)",
         labelloc=t, labeljust=c];
  node [fontname="Helvetica", fontsize=10, shape=record, style=filled, fillcolor="#eff6ff", color="#2563eb"];
  edge [fontname="Helvetica", fontsize=9, arrowtail=none, arrowhead=normal];

  subgraph cluster_use_case {
    label="Casos de Uso";
    style="filled,rounded"; color="#15803d"; fillcolor="#f0fdf4"; fontcolor="#14532d";
    node [shape=ellipse, fillcolor="#dcfce7", color="#16a34a"];
    Actor [label="Usuario /\nOperador", shape=actor, fillcolor="#f1f5f9", color="#475569"];
    UC1 [label="Monitorear Variable"];
    UC2 [label="Configurar Umbrales"];
    UC3 [label="Controlar Actuador (Manual/Auto)"];
    
    Actor -> UC1;
    Actor -> UC2;
    Actor -> UC3;
  }

  subgraph cluster_classes {
    label="Diagrama de Clases";
    style="filled,rounded"; color="#1d4ed8"; fillcolor="#eff6ff"; fontcolor="#1e3a8a";
    node [shape=record, fillcolor="#bfdbfe", color="#2563eb"];
    
    Controlador [label="{Controlador|+ PIN_SENSOR: int\l+ PIN_ACTUADOR: int\l+ umbral_alto: float\l+ umbral_bajo: float\l|+ setup(): void\l+ loop(): void\l}"];
    Sensor [label="{Sensor|+ pin: int\l|+ leer_valor(): float\l}"];
    Actuador [label="{Actuador|+ pin: int\l+ estado: bool\l|+ conmutar(bool): void\l}"];
    
    Controlador -> Sensor [label="1..* usa", arrowhead=vee];
    Controlador -> Actuador [label="1 usa", arrowhead=vee];
  }
}
""".strip()
    return render_graphviz(dot, png, svg, f"Diagramas UML – {project_title}",
                            write_fallback_png, write_fallback_svg)


# ── Flujo de señal (telecomunicaciones y procesamiento de datos) ───────────────
def generate_signal_flow_diagram(diagram_dir: Path, project_title: str,
                                 write_fallback_png=None, write_fallback_svg=None) -> Dict[str, Optional[Path]]:
    png = diagram_dir / "diagrama_flujo_senal.png"
    svg = diagram_dir / "diagrama_flujo_senal.svg"
    dot = r"""
digraph flujo_senal {
  rankdir=LR;
  graph [bgcolor="white", fontname="Helvetica", fontsize=12, pad="0.5",
         label="Diagrama de Flujo de Señal (Telecomunicaciones & Procesamiento)",
         labelloc=t, labeljust=c];
  node [fontname="Helvetica", fontsize=10, shape=box, style="filled,rounded", fillcolor="#ecfeff", color="#0891b2"];
  edge [fontname="Helvetica", fontsize=9, color="#0891b2", penwidth=1.5];

  SENS_PHYS [label="Entrada Física\n(Sensor)", shape=cylinder, fillcolor="#ffedd5", color="#c2410c"];
  TRANSDUCER [label="Transductor\n(Señal analógica cruda)"];
  FILTER_AMP [label="Filtro / Amp\n(Acondicionamiento)"];
  ADC_CONV   [label="Conversión ADC\n(Cuantización 12-bit)"];
  MCU_PROC   [label="Procesamiento MCU\n(Filtrado digital & Lógica)"];
  TX_UART    [label="Módulo UART\n(Serial TX)"];
  WIFI_TX    [label="Wi-Fi (MQTT/HTTP)\n(Modulación RF)"];
  CLOUD_RX   [label="Servidor Nube / Dashboard\n(Recepción de Datos)", shape=cloud, fillcolor="#eff6ff", color="#2563eb"];

  SENS_PHYS -> TRANSDUCER [label="Magnitud física"];
  TRANSDUCER -> FILTER_AMP [label="Tensión (V)"];
  FILTER_AMP -> ADC_CONV [label="V filtrada"];
  ADC_CONV -> MCU_PROC [label="Dato binario"];
  MCU_PROC -> TX_UART [label="Trama serial"];
  MCU_PROC -> WIFI_TX [label="Paquetes TCP/IP"];
  WIFI_TX -> CLOUD_RX [label="Radiofrecuencia (RF)"];
}
""".strip()
    return render_graphviz(dot, png, svg, f"Flujo de señal – {project_title}",
                            write_fallback_png, write_fallback_svg)


# ── Criterios de Aceptación del Diseño (Hardware) ─────────────────────────────
def build_acceptance_criteria(project_title: str) -> List[str]:
    return [
        "1. Estabilidad de Voltaje: La alimentación del microcontrolador debe mantenerse en 3.3 V ± 3% bajo carga máxima.",
        "2. Precisión del Sensor: La lectura del ADC debe tener un error de cuantización inferior al 2% en todo el rango operativo.",
        "3. Tiempo de Respuesta: El actuador debe responder en menos de 500 ms tras superar el umbral configurado.",
        "4. Histéresis de Control: No debe presentarse oscilación (chattering) del actuador en torno a los umbrales de decisión.",
        "5. Aislamiento Eléctrico: El optoacoplador debe garantizar un aislamiento galvánico de al menos 5 kV entre la etapa de control y la de potencia.",
        "6. Consumo Energético: El consumo total del sistema en modo reposo no debe superar los 50 mA, y en estado activo los 500 mA."
    ]