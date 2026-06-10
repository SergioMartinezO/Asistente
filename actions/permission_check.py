from typing import Dict, Any, Optional, Callable
from .base import BaseAction
import asyncio
import sys

# Import the runnable check function
from pathlib import Path
import importlib.util
import os

# Load scripts.check_permissions as a module without requiring package imports
spec = importlib.util.spec_from_file_location("check_permissions", os.path.join(Path(__file__).parents[1], 'scripts', 'check_permissions.py'))
check_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check_mod)


class PermissionCheckAction(BaseAction):
    @property
    def name(self) -> str:
        return "permission_check"

    @property
    def description(self) -> str:
        return "Comprueba permisos de escritura/lectura en carpetas del usuario. Parámetros: {'all': bool }"

    async def execute(self, parameters: Dict[str, Any], player: Optional[Any] = None, speak_callback: Optional[Callable[[str], None]] = None) -> str:
        all_flag = bool(parameters.get('all', False))
        # run the check in a thread to avoid blocking event loop
        loop = asyncio.get_running_loop()
        report = await loop.run_in_executor(None, check_mod.run_check, all_flag)
        return report


def permission_check(parameters: Dict[str, Any]) -> str:
    """Synchronous helper for legacy callers (AgentExecutor)._"""
    all_flag = bool(parameters.get('all', False))
    return check_mod.run_check(all_flag)
