from agent.error_handler import ErrorDecision, analyze_error
from agent.executor import AgentExecutor


def test_error_handler_max_attempts_uses_spanish_message():
    out = analyze_error(
        step={"step": 1, "tool": "web_search", "description": "buscar", "critical": False},
        error="timeout",
        attempt=2,
        max_attempts=2,
    )
    assert out["decision"] == ErrorDecision.REPLAN
    assert "sir" not in out["user_message"].lower()
    assert "enfoque" in out["user_message"].lower()


def test_executor_returns_spanish_when_plan_is_invalid(monkeypatch):
    monkeypatch.setattr("agent.executor.create_plan", lambda goal: {"goal": goal, "steps": []})
    ex = AgentExecutor()
    result = ex.execute("probar flujo")
    assert "plan válido" in result.lower()
    assert "sir" not in result.lower()
