from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict


class PersistenceStore:
    """Persistencia de configuración, memoria y logs para la nueva arquitectura."""

    def __init__(self, base_dir: Path) -> None:
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.base_dir / "config.json"
        self.memory_file = self.base_dir / "memory.json"
        self.log_file = self.base_dir / "events.log"

    def _read_json(self, path: Path) -> Dict[str, Any]:
        if not path.exists():
            return {}
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _write_json(self, path: Path, data: Dict[str, Any]) -> None:
        path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

    def save_config(self, data: Dict[str, Any]) -> None:
        self._write_json(self.config_file, data)

    def load_config(self) -> Dict[str, Any]:
        return self._read_json(self.config_file)

    def save_memory(self, data: Dict[str, Any]) -> None:
        self._write_json(self.memory_file, data)

    def load_memory(self) -> Dict[str, Any]:
        return self._read_json(self.memory_file)

    def append_log(self, event: str) -> None:
        with self.log_file.open("a", encoding="utf-8") as f:
            f.write(event + "\\n")
