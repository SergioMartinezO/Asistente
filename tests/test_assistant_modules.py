from pathlib import Path

from assistant_modules.backend.facade import RexAssistantBackend
from assistant_modules.electronics.module import ElectronicsModule
from assistant_modules.mathematics.module import MathematicsModule
from assistant_modules.security_control.module import SecurityControlModule


def test_electronics_ohm_law():
    res = ElectronicsModule.ohm_law(voltage=10, resistance=5)
    assert res.current == 2


def test_math_solve_2x2():
    x, y = MathematicsModule.solve_2x2(2, 1, 5, 1, -1, 1)
    assert round(x, 4) == 2.0
    assert round(y, 4) == 1.0


def test_security_scrub_text():
    scrubbed = SecurityControlModule.scrub_sensitive_text("TOKEN=abc")
    assert isinstance(scrubbed, str)


def test_backend_process_text_and_architecture_summary(tmp_path: Path):
    backend = RexAssistantBackend(base_dir=tmp_path)
    out = backend.process_text("Calcula un circuito con ley de ohm", channel="vscode")
    assert out.action == "electronics.solve"

    arch = backend.architecture_summary()
    assert "frontend" in arch
    assert "backend" in arch
    assert "integrations" in arch
    assert "persistence" in arch
