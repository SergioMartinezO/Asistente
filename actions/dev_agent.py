import subprocess
import sys
import json
import re
import time
import os
from pathlib import Path
from datetime import datetime, timezone

from core.output_policy import DEFAULT_REPORT_DIR


def get_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR         = get_base_dir()
API_CONFIG_PATH  = BASE_DIR / "config" / "api_keys.json"
REPORT_ROOT      = Path(DEFAULT_REPORT_DIR)
PROJECTS_DIR     = REPORT_ROOT / "RexProjects"
MAX_FIX_ATTEMPTS = 5
MODEL_PLANNER    = "gemini-2.5-flash"
MODEL_WRITER     = "gemini-2.5-flash"


def _ensure_projects_dir() -> Path:
    """Garantiza que los entregables se construyan en D:\\IA\\Asistente\\Report."""
    REPORT_ROOT.mkdir(parents=True, exist_ok=True)
    PROJECTS_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["REX_REPORT_DIR"] = str(REPORT_ROOT)
    return PROJECTS_DIR


def _write_manifest(
    project_dir: Path,
    project_name: str,
    description: str,
    language: str,
    run_command: str,
    dependencies: list[str],
    planned_files: list[dict],
    generated_file_paths: list[str],
    status: str,
    attempts: int,
    last_output: str,
    notes: str = "",
) -> Path:
    """Escribe un manifest de entrega para trazabilidad del proyecto."""
    manifest_path = project_dir / "manifest.json"
    payload = {
        "project_name": project_name,
        "description": description,
        "language": language,
        "status": status,
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "project_dir": str(project_dir),
        "run_command": run_command,
        "dependencies": dependencies or [],
        "planned_files": [f.get("path", "") for f in (planned_files or []) if f.get("path")],
        "generated_files": sorted([p for p in (generated_file_paths or []) if p]),
        "attempts": attempts,
        "last_output_preview": (last_output or "")[:1500],
        "notes": notes,
    }

    def _fallback_payload(reason: str) -> dict:
        return {
            "project_name": project_name,
            "status": "failed",
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "project_dir": str(project_dir),
            "notes": f"Manifest fallback generado automáticamente: {reason}",
        }

    try:
        manifest_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        # Fallback inmediato si falló la primera escritura.
        fb = _fallback_payload(f"error de escritura inicial: {e}")
        manifest_path.write_text(json.dumps(fb, indent=2, ensure_ascii=False), encoding="utf-8")

    # Verificación runtime: archivo debe existir y no estar vacío.
    try:
        if (not manifest_path.exists()) or manifest_path.stat().st_size <= 0:
            fb = _fallback_payload("archivo ausente o vacío tras escritura")
            manifest_path.write_text(json.dumps(fb, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        # Último intento best-effort para no salir sin manifest.
        fb = _fallback_payload(f"fallo en verificación final: {e}")
        try:
            manifest_path.write_text(json.dumps(fb, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception:
            pass

    return manifest_path

def _get_model(model_name: str):
    from core.config import genai_legacy as genai
    return genai.GenerativeModel(model_name)


def _strip_fences(text: str) -> str:
    text = text.strip()
    text = re.sub(r"^```[a-zA-Z]*\r?\n?", "", text)
    text = re.sub(r"\r?\n?```\s*$", "", text)
    return text.strip()


def _is_rate_limit(error: Exception) -> bool:
    msg = str(error).lower()
    return "429" in msg or "quota" in msg or "resource_exhausted" in msg


def _parse_traceback(output: str, project_files: list[str]) -> tuple[str | None, int | None]:

    pattern = re.compile(r'File ["\']([^"\']+\.py)["\'],\s+line\s+(\d+)', re.IGNORECASE)
    matches = pattern.findall(output)

    for raw_path, line_str in reversed(matches):
        raw_name = Path(raw_path).name
        for pf in project_files:
            if Path(pf).name == raw_name or pf == raw_path or raw_path.endswith(pf):
                return pf, int(line_str)

    return None, None


def _classify_error(output: str) -> str:

    low = output.lower()

    if any(x in low for x in ("no module named", "modulenotfounderror", "importerror")):
        return "dependency_error"

    if "syntaxerror" in low or "invalid syntax" in low:
        return "syntax_error"
    
    if "cannot import" in low or "importerror" in low:
        return "import_error"

    if any(x in low for x in (
        "traceback", "exception", "error:", "nameerror", "typeerror",
        "attributeerror", "valueerror", "keyerror", "indexerror",
        "zerodivisionerror", "filenotfounderror", "permissionerror",
    )):
        return "runtime_error"

    return "none"


def _has_error(output: str, run_command: str) -> bool:
    
    low = output.lower()

    if "timed out" in low:
        return False

    if not output.strip():
        return False

    error_type = _classify_error(output)
    return error_type != "none"

class RateLimitError(Exception):
    pass


def _plan_project(description: str, language: str) -> dict:
    model = _get_model(MODEL_PLANNER)

    prompt = f"""You are a senior software architect. Create a minimal, complete file plan for this project.

Language: {language}
Description: {description}

Return ONLY valid JSON — no markdown, no explanation:
{{
  "project_name": "snake_case_name",
  "entry_point": "main.py",
  "files": [
    {{
      "path": "main.py",
      "description": "Entry point — what it does and which modules it imports",
      "imports": ["utils.helpers", "core.engine"]
    }},
    {{
      "path": "utils/helpers.py",
      "description": "Helper utilities — what functions it exposes",
      "imports": []
    }}
  ],
  "run_command": "python main.py",
  "dependencies": ["requests"]
}}

Critical rules:
1. List files in DEPENDENCY ORDER — files with no imports come first, entry point comes last.
2. The "imports" field must list every other project module this file imports (dot-notation, e.g. "utils.helpers").
3. Keep it minimal — only files truly needed.
4. Entry point must be in the files list.
5. Use relative paths only (e.g. "utils/helpers.py", not absolute paths).
6. Standard library modules (os, sys, json, etc.) do NOT go in "dependencies".

JSON:"""

    try:
        response = model.generate_content(prompt)
        raw = _strip_fences(response.text)
        return json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"Planner returned invalid JSON: {e}\nRaw: {response.text[:300]}")
    except Exception as e:
        if _is_rate_limit(e):
            raise RateLimitError(str(e))
        raise

def _write_file(
    file_info: dict,
    project_description: str,
    all_files: list[dict],
    language: str,
    project_dir: Path,
    already_written: dict[str, str],
) -> str:
    model = _get_model(MODEL_WRITER)

    file_path = file_info["path"]
    file_desc = file_info.get("description", "")
    file_imports = file_info.get("imports", [])

    file_list = "\n".join(
        f"  [{i+1}] {f['path']}: {f.get('description', '')}"
        for i, f in enumerate(all_files)
    )

    dependency_context = ""
    for dep_dotted in file_imports:
        dep_path = dep_dotted.replace(".", "/") + ".py"
        if dep_path in already_written:
            code_snippet = already_written[dep_path][:2000]
            dependency_context += f"\n\n--- {dep_path} (you must import from this) ---\n{code_snippet}"

    lang_rules = ""
    if language.lower() == "python":
        lang_rules = """
Python-specific rules:
- Use type hints for all function signatures.
- Add docstrings for all public functions and classes.
- Use if __name__ == "__main__": guard in the entry point.
- For relative imports within the project, use: from utils.helpers import foo  (match the project structure exactly).
- Do NOT use implicit relative imports (from . import ...) unless it's a proper package with __init__.py.
- If this is a package subdirectory, create __init__.py files where needed."""
    elif language.lower() in ("javascript", "typescript", "js", "ts"):
        lang_rules = """
JS/TS-specific rules:
- Use ES modules (import/export), not CommonJS (require).
- Add JSDoc comments for all exported functions.
- Handle promise rejections with try/catch in async functions."""

    prompt = f"""You are a senior {language} developer writing production-quality code for a real project.

Project goal: {project_description}

Complete project file structure (in dependency order):
{file_list}

{f"Dependencies this file must import from other project files:{dependency_context}" if dependency_context else ""}

Your task: Write the complete, working code for: {file_path}
Purpose of this file: {file_desc}
{f"This file imports from: {', '.join(file_imports)}" if file_imports else "This file has no project-internal imports."}

{lang_rules}

General rules:
- Output ONLY raw code. Absolutely no explanation, no markdown, no triple backticks.
- Write COMPLETE, RUNNABLE code — no placeholders, no "# TODO", no "pass" stubs.
- Every import must either be from the standard library, listed dependencies, or the project files shown above.
- Match import paths EXACTLY to the file paths in the project structure (e.g. if file is "utils/helpers.py", import as "from utils.helpers import ...").
- Use proper error handling (try/except) where I/O or network calls are made.
- The code must work correctly when the project entry point is run from the project root directory.

Code for {file_path}:"""

    try:
        response = model.generate_content(prompt)
        code = _strip_fences(response.text)

        full_path = project_dir / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(code, encoding="utf-8")

        print(f"[DevAgent] ✅ Written: {file_path} ({len(code)} chars)")
        return code

    except Exception as e:
        if _is_rate_limit(e):
            raise RateLimitError(str(e))
        raise

def _install_dependencies(dependencies: list[str], project_dir: Path) -> str:
    if not dependencies:
        return "No external dependencies."

    to_install = []
    for dep in dependencies:
        pkg_name = re.split(r"[>=<!]", dep)[0].strip()
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", pkg_name],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            to_install.append(dep)
        else:
            print(f"[DevAgent] ✓ Already installed: {pkg_name}")

    if not to_install:
        return f"All dependencies already installed: {', '.join(dependencies)}"

    print(f"[DevAgent] 📦 Installing: {to_install}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install"] + to_install,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=120, cwd=str(project_dir)
        )
        if result.returncode == 0:
            return f"Installed: {', '.join(to_install)}"
        return f"Install warning (non-fatal): {result.stderr[:200]}"
    except subprocess.TimeoutExpired:
        return "Dependency install timed out (non-fatal)."
    except Exception as e:
        return f"Install error (non-fatal): {e}"

def _open_vscode(project_dir: Path) -> bool:
    vscode_candidates = [
        "code",
        rf"C:\Users\{Path.home().name}\AppData\Local\Programs\Microsoft VS Code\bin\code.cmd",
        r"C:\Program Files\Microsoft VS Code\bin\code.cmd",
    ]
    for cmd in vscode_candidates:
        try:
            subprocess.Popen(
                [cmd, str(project_dir)],
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            time.sleep(1.5)
            print(f"[DevAgent] 💻 VSCode opened: {project_dir}")
            return True
        except Exception:
            continue
    return False

def _run_project(run_command: str, project_dir: Path, timeout: int = 30) -> str:
    print(f"[DevAgent] 🚀 Running: {run_command}")
    try:
        parts = run_command.split()
        if parts[0].lower() == "python":
            parts[0] = sys.executable

        result = subprocess.run(
            parts,
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=timeout,
            cwd=str(project_dir)
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        combined_parts = []
        if stdout:
            combined_parts.append(f"STDOUT:\n{stdout}")
        if stderr:
            combined_parts.append(f"STDERR:\n{stderr}")

        return "\n\n".join(combined_parts) if combined_parts else "Ran with no output."

    except subprocess.TimeoutExpired:
        return f"Timed out after {timeout}s — long-running app (server/GUI) is likely working."
    except FileNotFoundError as e:
        return f"Command not found: {e}"
    except Exception as e:
        return f"Run error: {e}"

def _try_auto_install(error_output: str, project_dir: Path) -> bool:
    """ModuleNotFoundError varsa eksik paketi otomatik kurmaya çalışır."""
    pattern = re.compile(
        r"No module named ['\"]([a-zA-Z0-9_\-\.]+)['\"]", re.IGNORECASE
    )
    match = pattern.search(error_output)
    if not match:
        return False

    pkg = match.group(1).replace("_", "-").split(".")[0]
    print(f"[DevAgent] 🔧 Auto-installing missing package: {pkg}")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", pkg],
            capture_output=True, text=True,
            encoding="utf-8", errors="replace",
            timeout=60, cwd=str(project_dir)
        )
        return result.returncode == 0
    except Exception:
        return False

def _fix_files(
    error_output: str,
    project_description: str,
    all_files: list[dict],
    file_codes: dict[str, str],
    language: str,
    project_dir: Path,
    entry_point: str,
) -> dict[str, str]:

    model = _get_model(MODEL_PLANNER)

    error_file, error_line = _parse_traceback(error_output, list(file_codes.keys()))
    error_type = _classify_error(error_output)

    files_to_fix: list[str] = []

    if error_file:
        files_to_fix.append(error_file)
        if error_type == "import_error":
            for fi in all_files:
                if error_file.replace("/", ".").replace(".py", "") in fi.get("imports", []):
                    p = fi["path"]
                    if p not in files_to_fix:
                        files_to_fix.append(p)
    else:
        files_to_fix.append(entry_point)

    updated_codes: dict[str, str] = {}

    for fix_path in files_to_fix:
        current_code = file_codes.get(fix_path, "")

        other_ctx = ""
        for fp, code in file_codes.items():
            if fp != fix_path and code:
                snippet = code[:1500] + ("..." if len(code) > 1500 else "")
                other_ctx += f"\n--- {fp} ---\n{snippet}\n"

        line_hint = f"\nError appears to be near line {error_line} in this file." if (
            error_line and fix_path == error_file
        ) else ""

        prompt = f"""You are an expert {language} debugger. Fix the broken file below.

Project goal: {project_description}

All project files:
{chr(10).join(f"  - {f['path']}: {f.get('description', '')}" for f in all_files)}

Other files for context (read-only — fix only the target file):
{other_ctx[:3500]}

File to fix: {fix_path}{line_hint}
Error type: {error_type}

Error output:
{error_output[:2500]}

Current (broken) code:
{current_code}

Rules:
- Output ONLY the complete fixed code. No explanation, no markdown, no backticks.
- Fix ALL errors visible in the error output.
- Keep all existing correct logic — do not remove working features.
- Ensure import paths match the actual project file structure exactly.
- Do NOT introduce new bugs or remove error handling.

Fixed code for {fix_path}:"""

        try:
            response = model.generate_content(prompt)
            fixed = _strip_fences(response.text)

            full_path = project_dir / fix_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(fixed, encoding="utf-8")

            updated_codes[fix_path] = fixed
            print(f"[DevAgent] 🔧 Fixed: {fix_path}")

        except Exception as e:
            if _is_rate_limit(e):
                raise RateLimitError(str(e))
            print(f"[DevAgent] ⚠️ Could not fix {fix_path}: {e}")

    return updated_codes

def _build_project(
    description: str,
    language: str,
    project_name: str,
    timeout: int,
    speak=None,
    player=None,
) -> str:

    def log(msg: str):
        print(f"[DevAgent] {msg}")
        if player:
            player.write_log(f"[DevAgent] {msg}")

    def say(msg: str):
        log(msg)
        if speak:
            try:
                speak(msg)
            except Exception:
                pass

    def phase_update(n: int, total: int, status: str, percent: int, next_action: str):
        percent = max(0, min(100, int(percent)))
        phase_explanations = {
            1: "definir alcance, estructura de archivos, entrada y comando de ejecución",
            2: "generar código fuente y artefactos mínimos por archivo en orden de dependencias",
            3: "instalar dependencias y preparar entorno de ejecución del proyecto",
            4: "ejecutar, validar salida y corregir errores de forma iterativa",
            5: "cerrar entrega, confirmar estado final y reportar ruta de entregables",
        }
        phase_desc = phase_explanations.get(n, "completar tareas técnicas del proyecto")
        say(
            f"Fase {n}/{total}. "
            f"Estado: {status}. "
            f"Avance: {percent} por ciento. "
            f"Esta fase consiste en: {phase_desc}. "
            f"Siguiente acción: {next_action}."
        )

    def phase_start(n: int, total: int, title: str):
        base = int(((n - 1) / max(total, 1)) * 100)
        phase_update(n, total, "en curso", base, title)

    def phase_confirm(n: int, total: int, title: str):
        base = int((n / max(total, 1)) * 100)
        phase_update(n, total, "confirmada", base, f"pasar a la siguiente fase tras {title}")

    total_phases = 5
    projects_dir = _ensure_projects_dir()
    say(f"Los entregables se construirán en la ruta: {projects_dir}")
    phase_start(1, total_phases, "planificación del proyecto")

    log("Planning project structure...")
    try:
        plan = _plan_project(description, language)
    except RateLimitError:
        msg = "Se alcanzó el límite temporal del servicio. Intenta nuevamente en unos momentos."
        if speak: speak(msg)
        return msg
    except ValueError as e:
        msg = f"Planning failed: {e}"
        if speak: speak(msg)
        return msg

    phase_confirm(1, total_phases, "planificación del proyecto")

    proj_name    = project_name or plan.get("project_name", "rex_project")
    proj_name    = re.sub(r"[^\w\-]", "_", proj_name)
    project_dir  = projects_dir / proj_name
    project_dir.mkdir(parents=True, exist_ok=True)

    files        = plan.get("files", [])
    entry_point  = plan.get("entry_point", "main.py")
    run_command  = plan.get("run_command", f"python {entry_point}")
    dependencies = plan.get("dependencies", [])

    log(f"Project: {proj_name} | Files: {len(files)} | Entry: {entry_point}")

    def _dep_sort_key(fi: dict) -> int:
        return len(fi.get("imports", []))

    sorted_files = sorted(files, key=_dep_sort_key)

    file_codes: dict[str, str] = {}

    phase_start(2, total_phases, "generación de archivos del proyecto")

    total_files = len(sorted_files) if sorted_files else 0
    for idx, file_info in enumerate(sorted_files, 1):
        file_path = file_info.get("path", "")
        if not file_path:
            continue

        partial = 20 + int((idx / max(total_files, 1)) * 20)
        phase_update(
            2,
            total_phases,
            "en curso",
            partial,
            f"crear archivo {idx}/{max(total_files,1)}: {file_path}"
        )
        for attempt in range(2):
            try:
                code = _write_file(
                    file_info=file_info,
                    project_description=description,
                    all_files=files,
                    language=language,
                    project_dir=project_dir,
                    already_written=file_codes,
                )
                file_codes[file_path] = code
                time.sleep(0.4)
                break
            except RateLimitError:
                if attempt == 0:
                    log("Rate limit — waiting 20s...")
                    time.sleep(20)
                else:
                    log(f"Rate limit retry failed for {file_path}, skipping.")
            except Exception as e:
                log(f"Failed to write {file_path}: {e}")
                break

    if not file_codes:
        msg = "No pude generar archivos del proyecto."
        manifest_path = _write_manifest(
            project_dir=project_dir,
            project_name=proj_name,
            description=description,
            language=language,
            run_command=run_command,
            dependencies=dependencies,
            planned_files=files,
            generated_file_paths=[],
            status="failed",
            attempts=0,
            last_output="No se generaron archivos del proyecto.",
            notes="Finalizó tempranamente sin archivos generados.",
        )
        msg = f"{msg} Manifest: {manifest_path}."
        if speak: speak(msg)
        return msg

    phase_confirm(2, total_phases, "generación de archivos del proyecto")

    phase_start(3, total_phases, "dependencias y preparación de entorno")

    if dependencies:
        install_result = _install_dependencies(dependencies, project_dir)
        say(install_result)
    else:
        say("No se requieren dependencias externas adicionales.")

    _open_vscode(project_dir)
    phase_confirm(3, total_phases, "dependencias y preparación de entorno")

    last_output   = ""
    auto_installs = 0  

    phase_start(4, total_phases, "ejecución y validación por intentos")

    for attempt in range(1, MAX_FIX_ATTEMPTS + 1):
        partial = 60 + int((attempt / max(MAX_FIX_ATTEMPTS, 1)) * 20)
        phase_update(
            4,
            total_phases,
            "en curso",
            partial,
            f"ejecutar intento {attempt}/{MAX_FIX_ATTEMPTS}"
        )
        last_output = _run_project(run_command, project_dir, timeout)
        log(f"Output preview: {last_output[:150]}")

        if not _has_error(last_output, run_command):
            phase_confirm(4, total_phases, "ejecución y validación por intentos")
            phase_start(5, total_phases, "cierre y entrega")
            manifest_path = _write_manifest(
                project_dir=project_dir,
                project_name=proj_name,
                description=description,
                language=language,
                run_command=run_command,
                dependencies=dependencies,
                planned_files=files,
                generated_file_paths=list(file_codes.keys()),
                status="success",
                attempts=attempt,
                last_output=last_output,
                notes="Construcción y validación completadas correctamente.",
            )
            msg = (
                f"Proyecto '{proj_name}' operativo. "
                f"Construcción completada en {attempt} intento{'s' if attempt > 1 else ''}. "
                f"Ruta de entrega: {project_dir}. "
                f"Manifest: {manifest_path}. "
                "Pasos informados y confirmados por fase."
            )
            if speak: speak(msg)
            phase_confirm(5, total_phases, "cierre y entrega")
            return f"{msg}\n\nOutput:\n{last_output}"

        if attempt == MAX_FIX_ATTEMPTS:
            break

        error_type = _classify_error(last_output)
        if error_type == "dependency_error" and auto_installs < 3:
            installed = _try_auto_install(last_output, project_dir)
            if installed:
                auto_installs += 1
                phase_update(
                    4,
                    total_phases,
                    "en curso",
                    partial,
                    "dependencia instalada; reintentar validación"
                )
                time.sleep(1)
                continue

        phase_update(
            4,
            total_phases,
            "bloqueada",
            partial,
            f"corregir error de tipo {error_type}"
        )
        try:
            updated = _fix_files(
                error_output=last_output,
                project_description=description,
                all_files=files,
                file_codes=file_codes,
                language=language,
                project_dir=project_dir,
                entry_point=entry_point,
            )
            file_codes.update(updated)
            time.sleep(1)
        except RateLimitError:
            msg = "Se alcanzó el límite durante la corrección. El proyecto quedó guardado para revisión manual en VSCode."
            manifest_path = _write_manifest(
                project_dir=project_dir,
                project_name=proj_name,
                description=description,
                language=language,
                run_command=run_command,
                dependencies=dependencies,
                planned_files=files,
                generated_file_paths=list(file_codes.keys()),
                status="failed",
                attempts=attempt,
                last_output=last_output,
                notes="Rate limit durante fase de corrección.",
            )
            msg = f"{msg} Manifest: {manifest_path}."
            if speak: speak(msg)
            return msg
        except Exception as e:
            log(f"Fix step failed: {e}")

    msg = (
        f"No fue posible dejar '{proj_name}' totalmente estable tras {MAX_FIX_ATTEMPTS} intentos. "
        f"Proyecto guardado en {project_dir}. "
        "Confirmo fin de fase de validación con incidencias pendientes para revisión manual."
    )
    manifest_path = _write_manifest(
        project_dir=project_dir,
        project_name=proj_name,
        description=description,
        language=language,
        run_command=run_command,
        dependencies=dependencies,
        planned_files=files,
        generated_file_paths=list(file_codes.keys()),
        status="failed",
        attempts=MAX_FIX_ATTEMPTS,
        last_output=last_output,
        notes="Finalizó con incidencias pendientes para revisión manual.",
    )
    msg = f"{msg} Manifest: {manifest_path}."
    if speak: speak(msg)
    return f"{msg}\n\nLast error:\n{last_output[:600]}"


def dev_agent(
    parameters: dict,
    response=None,
    player=None,
    session_memory=None,
    speak=None,
) -> str:
    p            = parameters or {}
    description  = p.get("description", "").strip()
    language     = p.get("language", "python").strip()
    project_name = p.get("project_name", "").strip()
    timeout      = int(p.get("timeout", 30))

    if not description:
        return "Describe el proyecto que deseas construir para iniciar por fases."

    return _build_project(
        description  = description,
        language     = language,
        project_name = project_name,
        timeout      = timeout,
        speak        = speak,
        player       = player,
    )