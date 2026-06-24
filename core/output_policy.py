from __future__ import annotations

import os
from pathlib import Path
from typing import Dict, Any

DEFAULT_REPORT_DIR = Path(r"D:\IA\Asistente\Report")


def get_report_base() -> Path:
    base = Path(os.environ.get("REX_REPORT_DIR", str(DEFAULT_REPORT_DIR))).expanduser()
    base.mkdir(parents=True, exist_ok=True)
    return base


def resolve_output_file(requested_path: str | None, default_name: str) -> str:
    base = get_report_base()
    if not requested_path:
        return str(base / default_name)
    p = Path(str(requested_path)).expanduser()
    if p.is_absolute():
        return str(base / p.name)
    return str(base / p)


def resolve_output_dir(requested_path: str | None, default_name: str = "") -> str:
    base = get_report_base()
    if not requested_path:
        target = base / default_name if default_name else base
    else:
        p = Path(str(requested_path)).expanduser()
        target = (base / p.name) if p.is_absolute() else (base / p)
    target.mkdir(parents=True, exist_ok=True)
    return str(target)


def normalize_tool_outputs(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(args or {})

    if tool_name == "engineering_report":
        out["output_docx"] = resolve_output_file(out.get("output_docx"), "Reporte_Proyecto.docx")
        out["output_html"] = resolve_output_file(out.get("output_html"), "index.html")
        out["diagram_dir"] = resolve_output_dir(out.get("diagram_dir"), "diagramas")

    elif tool_name == "code_helper":
        out["output_path"] = resolve_output_file(out.get("output_path"), "rex_code.py")

    elif tool_name == "file_processor":
        out["output_dir"] = resolve_output_dir(out.get("output_dir"), "")
        if (out.get("action") or "").lower() == "extract":
            out["destination"] = resolve_output_dir(out.get("destination"), "extract")

    elif tool_name == "browser_control" and (out.get("action") or "").lower() == "screenshot":
        out["path"] = resolve_output_file(out.get("path"), "rex_browser_screenshot.png")

    elif tool_name == "computer_control" and (out.get("action") or "").lower() == "screenshot":
        out["path"] = resolve_output_file(out.get("path"), "rex_screenshot.png")

    return out
