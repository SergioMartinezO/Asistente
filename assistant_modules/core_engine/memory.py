from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class UserMemoryManager:
    """Memoria/persistencia de preferencias de usuario para el nuevo backend modular."""

    def __init__(self, memory_file: Path) -> None:
        self.memory_file = memory_file
        self.memory_file.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> Dict[str, Any]:
        if not self.memory_file.exists():
            return {"preferences": {}, "context": {}}
        try:
            return json.loads(self.memory_file.read_text(encoding="utf-8"))
        except Exception:
            return {"preferences": {}, "context": {}}

    def save(self, data: Dict[str, Any]) -> None:
        self.memory_file.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def set_preference(self, key: str, value: Any) -> None:
        data = self.load()
        data.setdefault("preferences", {})[key] = value
        self.save(data)

    def get_preference(self, key: str, default: Any = None) -> Any:
        return self.load().get("preferences", {}).get(key, default)
