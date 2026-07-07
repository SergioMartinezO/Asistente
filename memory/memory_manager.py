import json
import re
from datetime import datetime
from threading import Lock
from pathlib import Path
import sys


def get_base_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent


BASE_DIR         = get_base_dir()
MEMORY_PATH      = BASE_DIR / "memory" / "long_term.json"
TECH_MEMORY_PATH = BASE_DIR / "memory" / "technical_memory.json"
_lock            = Lock()
MAX_VALUE_LENGTH = 380
MEMORY_MAX_CHARS = 2200

# ── Categorías técnicas por dominio de ingeniería ─────────────────────────────
_TECH_CATEGORIES = {
    "electronica":   ["circuito", "resistencia", "condensador", "transistor", "op-amp",
                      "ltspice", "proteus", "pcb", "arduino", "esp32", "voltaje", "corriente",
                      "ohm", "amplificador", "diodo", "oscilador", "filtro", "señal", "sensor"],
    "mecatronica":   ["servo", "motor", "encoder", "pid", "actuador", "robot", "cnc",
                      "stepper", "pwm", "torque", "velocidad", "posicion", "control",
                      "mecatronica", "automatizacion", "plc"],
    "software":      ["python", "codigo", "error", "excepcion", "modulo", "script", "debug",
                      "funcion", "clase", "api", "json", "asyncio", "thread", "git",
                      "dependencia", "import", "variable", "loop", "compilar"],
    "soluciones":    ["solucion", "fix", "corregido", "resuelto", "trabajando", "funciona",
                      "arreglado", "parche", "workaround", "causa", "raiz"],
}

_TECH_KEYWORDS = {kw: cat for cat, kws in _TECH_CATEGORIES.items() for kw in kws}


def _detect_tech_category(text: str) -> str | None:
    """Detecta la categoría técnica predominante de un texto por frecuencia de keywords."""
    low = text.lower()
    scores: dict[str, int] = {}
    for word in re.findall(r"[a-záéíóúñ]+", low):
        cat = _TECH_KEYWORDS.get(word)
        if cat:
            scores[cat] = scores.get(cat, 0) + 1
    return max(scores, key=scores.get) if scores else None


def _load_tech_memory() -> dict:
    if not TECH_MEMORY_PATH.exists():
        return {cat: {} for cat in _TECH_CATEGORIES}
    try:
        data = json.loads(TECH_MEMORY_PATH.read_text(encoding="utf-8"))
        for cat in _TECH_CATEGORIES:
            data.setdefault(cat, {})
        return data
    except Exception:
        return {cat: {} for cat in _TECH_CATEGORIES}


def save_tech_memory(tech_mem: dict) -> None:
    TECH_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        TECH_MEMORY_PATH.write_text(
            json.dumps(tech_mem, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def remember_technical(key: str, value: str, category: str | None = None) -> str:
    """Guarda una solución o conocimiento técnico con categoría auto-detectada."""
    if not category:
        category = _detect_tech_category(f"{key} {value}") or "soluciones"
    if category not in _TECH_CATEGORIES:
        category = "soluciones"
    tech_mem = _load_tech_memory()
    tech_mem[category][key] = {
        "value": value[:600],
        "updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "category": category,
    }
    save_tech_memory(tech_mem)
    return f"Solución técnica guardada en [{category}]: {key}"


def recall_technical(query: str, top_k: int = 5) -> list[dict]:
    """Recupera soluciones técnicas relevantes para una consulta por similitud de keywords."""
    tech_mem = _load_tech_memory()
    query_words = set(re.findall(r"[a-záéíóúñ]+", query.lower()))
    results = []
    for cat, entries in tech_mem.items():
        for key, entry in entries.items():
            if not isinstance(entry, dict):
                continue
            entry_text = f"{key} {entry.get('value', '')}".lower()
            entry_words = set(re.findall(r"[a-záéíóúñ]+", entry_text))
            score = len(query_words & entry_words)
            if score > 0:
                results.append({
                    "key": key,
                    "value": entry.get("value", ""),
                    "category": cat,
                    "score": score,
                    "updated": entry.get("updated", ""),
                })
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def format_tech_memory_for_prompt(query: str = "") -> str:
    """Formatea las soluciones técnicas más relevantes para incluir en el prompt del sistema."""
    if query:
        results = recall_technical(query, top_k=4)
    else:
        tech_mem = _load_tech_memory()
        results = []
        for cat, entries in tech_mem.items():
            for key, entry in list(entries.items())[-2:]:
                if isinstance(entry, dict):
                    results.append({"key": key, "value": entry.get("value", ""),
                                    "category": cat, "updated": entry.get("updated", "")})
    if not results:
        return ""
    lines = ["[MEMORIA TÉCNICA — soluciones previas relevantes]"]
    for r in results:
        lines.append(f"  [{r['category'].upper()}] {r['key']}: {r['value'][:180]}")
    return "\n".join(lines) + "\n"


def _empty_memory() -> dict:
    return {
        "identity":      {},
        "preferences":   {},
        "projects":      {},
        "relationships": {},
        "wishes":        {},
        "notes":         {},
    }

def load_memory() -> dict:
    if not MEMORY_PATH.exists():
        return _empty_memory()
    with _lock:
        try:
            data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                base = _empty_memory()
                for key in base:
                    if key not in data:
                        data[key] = {}
                return data
            return _empty_memory()
        except Exception as e:
            print(f"[Memory] ⚠️ Load error: {e}")
            return _empty_memory()

def _all_entries(memory: dict) -> list[tuple]:
    entries = []
    for cat, items in memory.items():
        if not isinstance(items, dict):
            continue
        for key, entry in items.items():
            if isinstance(entry, dict) and "value" in entry:
                entries.append((cat, key, entry))
    return entries


def _trim_to_limit(memory: dict) -> dict:
    if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
        return memory
    entries = _all_entries(memory)
    entries.sort(key=lambda t: t[2].get("updated", "0000-00-00"))
    for cat, key, _ in entries:
        if len(json.dumps(memory, ensure_ascii=False)) <= MEMORY_MAX_CHARS:
            break
        del memory[cat][key]
        print(f"[Memory] 🗑️  Trimmed {cat}/{key}")
    return memory

def save_memory(memory: dict) -> None:
    if not isinstance(memory, dict):
        return
    memory = _trim_to_limit(memory)
    MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _lock:
        MEMORY_PATH.write_text(
            json.dumps(memory, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )


def _truncate_value(val: str) -> str:
    if isinstance(val, str) and len(val) > MAX_VALUE_LENGTH:
        return val[:MAX_VALUE_LENGTH].rstrip() + "…"
    return val


def _recursive_update(target: dict, updates: dict) -> bool:
    changed = False
    for key, value in updates.items():
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        if isinstance(value, dict) and "value" not in value:
            if key not in target or not isinstance(target[key], dict):
                target[key] = {}
                changed = True
            if _recursive_update(target[key], value):
                changed = True
        else:
            new_val  = _truncate_value(str(value["value"] if isinstance(value, dict) else value))
            entry    = {"value": new_val, "updated": datetime.now().strftime("%Y-%m-%d")}
            existing = target.get(key, {})
            if not isinstance(existing, dict) or existing.get("value") != new_val:
                target[key] = entry
                changed = True
    return changed


def update_memory(memory_update: dict) -> dict:
    if not isinstance(memory_update, dict) or not memory_update:
        return load_memory()
    with _lock:
        # Cargamos memoria (omitimos _lock interno en load_memory reusando su lógica interna o simplemente adquiriendo el lock de forma recursiva si fuera RLock,
        # pero dado que es Lock normal, simulamos la lectura segura interna para evitar interbloqueo si load_memory intentara adquirir el mismo lock).
        # Para evitar interbloqueos, cargamos manualmente de forma no bloqueante o llamando a una subfunción:
        memory = _empty_memory()
        if MEMORY_PATH.exists():
            try:
                data = json.loads(MEMORY_PATH.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    base = _empty_memory()
                    for key in base:
                        if key not in data:
                            data[key] = {}
                    memory = data
            except Exception as e:
                print(f"[Memory] ⚠️ Load error in update_memory: {e}")
        
        if _recursive_update(memory, memory_update):
            # Guardado directo simplificado bajo el mismo lock
            memory = _trim_to_limit(memory)
            MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
            MEMORY_PATH.write_text(
                json.dumps(memory, indent=2, ensure_ascii=False),
                encoding="utf-8",
            )
            print(f"[Memory] 💾 Saved: {list(memory_update.keys())}")
        return memory


def format_memory_for_prompt(memory: dict | None) -> str:
    if not memory:
        return ""

    lines = []

    identity  = memory.get("identity", {})
    id_fields = ["name", "age", "birthday", "city", "job", "language", "school", "nationality"]
    for field in id_fields:
        entry = identity.get(field)
        if entry:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"{field.title()}: {val}")
    for key, entry in identity.items():
        if key in id_fields:
            continue
        val = entry.get("value") if isinstance(entry, dict) else entry
        if val:
            lines.append(f"{key.replace('_', ' ').title()}: {val}")

    prefs = memory.get("preferences", {})
    if prefs:
        lines.append("")
        lines.append("Preferences:")
        for key, entry in list(prefs.items())[:15]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    projects = memory.get("projects", {})
    if projects:
        lines.append("")
        lines.append("Active Projects / Goals:")
        for key, entry in list(projects.items())[:8]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    rels = memory.get("relationships", {})
    if rels:
        lines.append("")
        lines.append("People in their life:")
        for key, entry in list(rels.items())[:10]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    wishes = memory.get("wishes", {})
    if wishes:
        lines.append("")
        lines.append("Wishes / Plans / Wants:")
        for key, entry in list(wishes.items())[:8]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key.replace('_', ' ').title()}: {val}")

    notes = memory.get("notes", {})
    if notes:
        lines.append("")
        lines.append("Other notes:")
        for key, entry in list(notes.items())[:8]:
            val = entry.get("value") if isinstance(entry, dict) else entry
            if val:
                lines.append(f"  - {key}: {val}")

    if not lines:
        return ""

    header = "[WHAT YOU KNOW ABOUT THIS PERSON — use naturally, never recite like a list]\n"
    result = header + "\n".join(lines)
    if len(result) > 2000:
        result = result[:1997] + "…"

    return result + "\n"

def remember(key: str, value: str, category: str = "notes") -> str:
    valid = {"identity", "preferences", "projects", "relationships", "wishes", "notes"}
    if category not in valid:
        category = "notes"
    update_memory({category: {key: {"value": value}}})
    return f"Remembered: {category}/{key} = {value}"


def forget(key: str, category: str = "notes") -> str:
    memory = load_memory()
    cat    = memory.get(category, {})
    if key in cat:
        del cat[key]
        memory[category] = cat
        save_memory(memory)
        return f"Forgotten: {category}/{key}"
    return f"Not found: {category}/{key}"


forget_memory = forget