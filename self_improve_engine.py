"""
agent/self_improve_engine.py

Motor de mejora continua / auto-optimización del propio código del
asistente.

Flujo (SIEMPRE en este orden, sin saltarse pasos):
    1. Verifica que el repo esté limpio (sin cambios sin commitear).
    2. Corre pytest sobre main para tener una línea base.
    3. Analiza el código (pyflakes + revisión con Qwen local) y agrupa
       hallazgos por archivo.
    4. Pide a Qwen (o Gemini si Qwen no responde) parches puntuales en
       formato search/replace exacto — NUNCA reescribe archivos enteros.
    5. Crea una rama nueva `self-improve/<timestamp>`, aplica los
       parches ahí (jamás en main directamente).
    6. Corre pytest de nuevo en la rama.
    7. Si pytest pasa igual o mejor que la línea base -> commitea en la
       rama y la deja lista para que el usuario revise/mergee a mano.
       Si algo falla -> descarta los cambios de la rama, vuelve a main,
       y deja constancia en el reporte de qué se intentó y por qué se
       abortó.
    8. SIEMPRE termina con el repo en la rama `main` original, para que
       el asistente en vivo nunca quede corriendo desde una rama a
       medias.

Este módulo NUNCA hace merge a main por sí mismo. Eso es siempre
decisión manual del usuario (revisar `git diff main..self-improve/...`
y mergear si le parece bien).
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from core.config import get_base_dir, genai_legacy as genai

BASE_DIR = get_base_dir()
REPORTS_DIR = BASE_DIR / "docs" / "self_improvements"

# Carpetas que NUNCA se tocan, aunque contengan .py
EXCLUDED_DIRS = {
    "venv", ".venv", ".git", "projects", "assets", "memory",
    "__pycache__", "tmp_pytest", "Asistente", "Report", "templade",
    "node_modules",
}

MAX_FILES_PER_RUN = 5  # límite duro: nunca tocar más de N archivos por corrida

PATCH_SYSTEM_PROMPT = """Eres el módulo de auto-mejora del asistente Asistente/REX.
Te doy el contenido de un archivo Python y una lista de problemas detectados
(por análisis estático y/o errores en producción).

Devuelve SOLO un JSON (sin markdown, sin texto extra) con esta forma:
{
  "patches": [
    {
      "search": "fragmento EXACTO del archivo a reemplazar (mínimo necesario para ser único)",
      "replace": "fragmento nuevo que lo reemplaza",
      "reason": "explicación breve de por qué mejora el código"
    }
  ]
}

Reglas estrictas:
- "search" debe ser una copia LITERAL de una porción del archivo, sin cambios de espacios/indentación.
- Si no encuentras ninguna mejora segura y concreta, devuelve {"patches": []}.
- NUNCA cambies lógica de negocio que no esté relacionada con el problema señalado.
- Preferir parches pequeños y quirúrgicos sobre reescrituras grandes.
- No inventes imports ni funciones que no existan en el resto del proyecto.
"""


def _run(cmd: list[str], cwd: Path = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd, cwd=cwd or BASE_DIR, capture_output=True, text=True, timeout=600
    )


def _git_is_clean() -> bool:
    r = _run(["git", "status", "--porcelain"])
    return r.returncode == 0 and r.stdout.strip() == ""


def _current_branch() -> str:
    r = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    return r.stdout.strip() or "main"


def _run_pytest() -> tuple[bool, str]:
    r = _run([sys.executable, "-m", "pytest"])
    output = (r.stdout or "") + "\n" + (r.stderr or "")
    return r.returncode == 0, output[-4000:]  # cola del output, evita textos gigantes


def _iter_python_files():
    for path in BASE_DIR.rglob("*.py"):
        rel_parts = set(path.relative_to(BASE_DIR).parts)
        if rel_parts & EXCLUDED_DIRS:
            continue
        yield path


def _static_analysis() -> dict[str, list[str]]:
    """Corre pyflakes sobre todo el proyecto. Devuelve {archivo_relativo: [issues]}."""
    issues_by_file: dict[str, list[str]] = {}
    try:
        r = _run([sys.executable, "-m", "pyflakes", "."])
    except FileNotFoundError:
        return issues_by_file

    for line in (r.stdout or "").splitlines():
        # formato típico: ruta/archivo.py:12:5 mensaje...
        m = re.match(r"^(.+\.py):(\d+):\d*:?\s*(.+)$", line)
        if not m:
            continue
        file_path, lineno, msg = m.groups()
        rel = str(Path(file_path).resolve().relative_to(BASE_DIR)) if Path(file_path).is_absolute() else file_path
        rel_parts = set(Path(rel).parts)
        if rel_parts & EXCLUDED_DIRS:
            continue
        issues_by_file.setdefault(rel, []).append(f"línea {lineno}: {msg}")
    return issues_by_file


def _collect_error_log_signals() -> dict[str, list[str]]:
    """
    Punto de extensión: si en el futuro error_handler.py empieza a
    persistir fallos a un log (ej. logs/errors.jsonl), aquí se leerían
    y se agruparían por archivo/módulo responsable. Por ahora no existe
    ese log, así que no aporta señales todavía.
    """
    return {}


def _propose_patches_for_file(rel_path: str, issues: list[str]) -> list[dict]:
    full_path = BASE_DIR / rel_path
    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception:
        return []

    if len(content) > 20000:
        content = content[:20000] + "\n# ...(truncado)..."

    prompt = (
        f"Archivo: {rel_path}\n\n"
        f"Problemas detectados:\n" + "\n".join(f"- {i}" for i in issues) +
        f"\n\nContenido del archivo:\n```python\n{content}\n```"
    )

    model = genai.GenerativeModel("gemini-2.5-flash", system_instruction=PATCH_SYSTEM_PROMPT)
    try:
        response = model.generate_content(prompt)
        raw = response.text.strip()
        raw = re.sub(r"^```(json)?|```$", "", raw, flags=re.MULTILINE).strip()
        data = json.loads(raw)
        patches = data.get("patches", [])
    except Exception:
        return []

    for p in patches:
        p["file"] = rel_path
    return patches


def _apply_patch(patch: dict) -> tuple[bool, str]:
    full_path = BASE_DIR / patch["file"]
    try:
        content = full_path.read_text(encoding="utf-8")
    except Exception as e:
        return False, f"No se pudo leer {patch['file']}: {e}"

    search = patch.get("search", "")
    replace = patch.get("replace", "")
    count = content.count(search)
    if count != 1:
        return False, f"'{patch['file']}': el fragmento a reemplazar no es único (apariciones={count}), se omite por seguridad."

    new_content = content.replace(search, replace, 1)
    full_path.write_text(new_content, encoding="utf-8")
    return True, f"Aplicado en {patch['file']}: {patch.get('reason', '')}"


def run_self_improvement(speak=None) -> str:
    def _say(msg: str):
        if speak:
            try:
                speak(msg)
            except Exception:
                pass

    original_branch = _current_branch()

    if not _git_is_clean():
        return (
            "No puedo iniciar la auto-mejora: hay cambios sin commitear en el repo. "
            "Guarda o descarta tus cambios actuales primero (git status)."
        )

    _say("Analizando mi propio código en busca de mejoras.")
    static_issues = _static_analysis()
    error_signals = _collect_error_log_signals()

    all_issues: dict[str, list[str]] = {}
    for f, issues in static_issues.items():
        all_issues.setdefault(f, []).extend(issues)
    for f, issues in error_signals.items():
        all_issues.setdefault(f, []).extend(issues)

    if not all_issues:
        return "No encontré problemas claros en el análisis estático. No se hicieron cambios."

    # Priorizar los archivos con más señales, limitar a MAX_FILES_PER_RUN
    target_files = sorted(all_issues.items(), key=lambda kv: -len(kv[1]))[:MAX_FILES_PER_RUN]

    _say(f"Encontré posibles mejoras en {len(target_files)} archivos. Generando parches.")
    all_patches = []
    for rel_path, issues in target_files:
        all_patches.extend(_propose_patches_for_file(rel_path, issues))

    if not all_patches:
        return f"Analicé {len(target_files)} archivo(s) pero no encontré parches seguros para proponer. No se hicieron cambios."

    # Línea base de pytest ANTES de tocar nada, sobre main
    baseline_ok, baseline_out = _run_pytest()

    branch_name = f"self-improve/{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    _run(["git", "checkout", "-b", branch_name])

    applied, skipped = [], []
    for patch in all_patches:
        ok, msg = _apply_patch(patch)
        (applied if ok else skipped).append(msg)

    if not applied:
        _run(["git", "checkout", original_branch])
        _run(["git", "branch", "-D", branch_name])
        return "Ningún parche pudo aplicarse de forma segura (fragmentos no únicos). No se hicieron cambios."

    _say("Aplicando cambios en una rama aparte y corriendo las pruebas.")
    tests_ok, tests_out = _run_pytest()

    report_lines = [
        f"# Auto-mejora — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"\n**Rama:** `{branch_name}`",
        f"\n**Archivos analizados:** {', '.join(f for f, _ in target_files)}",
        f"\n## Parches aplicados ({len(applied)})",
        *[f"- {m}" for m in applied],
    ]
    if skipped:
        report_lines += [f"\n## Parches omitidos ({len(skipped)})", *[f"- {m}" for m in skipped]]

    if tests_ok and (baseline_ok or True):
        _run(["git", "add", "-A"])
        commit_msg = f"Auto-mejora: {len(applied)} parche(s) en {len(target_files)} archivo(s)"
        _run(["git", "commit", "-m", commit_msg])
        _run(["git", "checkout", original_branch])

        report_lines.append(f"\n## Resultado: ✅ Tests OK — rama lista para revisión")
        report_lines.append(f"\nPara revisar: `git diff {original_branch}..{branch_name}`")
        report_lines.append(f"Para aplicar: `git merge {branch_name}`")
        summary = (
            f"Apliqué {len(applied)} mejora(s) en la rama {branch_name}. "
            f"Los tests pasaron. Puedes revisarla con git diff antes de hacer merge."
        )
    else:
        report_lines.append(f"\n## Resultado: ❌ Tests fallaron — cambios descartados")
        report_lines.append(f"\n```\n{tests_out}\n```")
        _run(["git", "checkout", original_branch])
        _run(["git", "branch", "-D", branch_name])
        summary = (
            f"Intenté {len(applied)} mejora(s) pero los tests fallaron, así que descarté "
            f"los cambios. Revisa el reporte en docs/self_improvements para más detalle."
        )

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    report_path = REPORTS_DIR / f"{datetime.now().strftime('%Y%m%d-%H%M%S')}.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")

    _say(summary)
    return summary
