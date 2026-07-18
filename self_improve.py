"""
actions/self_improve.py

Acción manual: "Rex, mejórate" / "analiza y mejora tu código".
Delega toda la lógica real a agent/self_improve_engine.py.
"""

from agent.self_improve_engine import run_self_improvement


def self_improve(parameters: dict = None, response=None, player=None,
                  session_memory=None, speak=None) -> str:
    return run_self_improvement(speak=speak)
