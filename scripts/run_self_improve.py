"""
scripts/run_self_improve.py

Entrypoint headless (sin UI ni voz) para disparar la auto-mejora desde
el Programador de tareas de Windows.

Uso programado (ejemplo, cada domingo 3 AM):
    Programa: D:\\IA\\Asistente\\venv\\Scripts\\python.exe
    Argumentos: D:\\IA\\Asistente\\scripts\\run_self_improve.py
    Iniciar en: D:\\IA\\Asistente

No corras esto al mismo tiempo que el asistente está activo en vivo:
ambos comparten el mismo repo git y podrían pisarse si el usuario tiene
cambios sin commitear justo en ese momento (el motor aborta solo si
detecta el repo sucio, pero mejor programarlo en horas de bajo uso).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent.self_improve_engine import run_self_improvement

if __name__ == "__main__":
    result = run_self_improvement(speak=None)
    print(result)
