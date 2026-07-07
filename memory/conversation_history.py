import json
import os
from datetime import datetime
from pathlib import Path

def get_history_path():
    import sys
    if getattr(sys, "frozen", False):
        base = Path(sys.executable).parent / "memory"
    else:
        base = Path(__file__).resolve().parent
    base.mkdir(parents=True, exist_ok=True)
    return base / "conversation_history.json"


def load_history() -> list:
    path = get_history_path()
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def save_session(session: list):
    if not session:
        return
    history = load_history()
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "messages": session[-40:]  # máximo 40 mensajes por sesión
    }
    history.append(entry)
    # mantener solo las últimas 10 sesiones
    history = history[-10:]
    path = get_history_path()
    with open(path, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def get_last_session_summary() -> str:
    history = load_history()
    if not history:
        return ""
    last = history[-1]
    date = last.get("date", "")
    messages = last.get("messages", [])
    if not messages:
        return ""
    lines = [f"[ÚLTIMA SESIÓN: {date}]"]
    for msg in messages[-10:]:  # últimos 10 mensajes
        role = msg.get("role", "")
        text = msg.get("text", "")
        if role and text:
            lines.append(f"{role.upper()}: {text}")
    return "\n".join(lines)

def format_history_for_prompt() -> str:
    summary = get_last_session_summary()
    if not summary:
        return ""
    return (
        "[HISTORIAL DE CONVERSACIÓN ANTERIOR]\n"
        f"{summary}\n"
        "Usa este contexto para dar continuidad a la conversación.\n\n"
    )