from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


@dataclass
class PermissionCheckResult:
    path: str
    readable: bool
    writable: bool
    executable: bool


class SecurityControlModule:
    """Gestión de permisos, protección de datos sensibles y cierre seguro."""

    SENSITIVE_ENV_KEYS = ("API_KEY", "TOKEN", "SECRET", "PASSWORD")

    @staticmethod
    def check_permissions(paths: Iterable[Path]) -> List[PermissionCheckResult]:
        results: List[PermissionCheckResult] = []
        for p in paths:
            results.append(
                PermissionCheckResult(
                    path=str(p),
                    readable=os.access(p, os.R_OK),
                    writable=os.access(p, os.W_OK),
                    executable=os.access(p, os.X_OK),
                )
            )
        return results

    @classmethod
    def scrub_sensitive_text(cls, text: str) -> str:
        redacted = text
        for key in cls.SENSITIVE_ENV_KEYS:
            val = os.getenv(key)
            if val:
                redacted = redacted.replace(val, f"***{key}***")
        return redacted

    @staticmethod
    def secure_shutdown_message() -> str:
        return "Cierre seguro solicitado: guardando estado, limpiando recursos y finalizando sesión."
