from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

from assistant_modules.automation_workflow.module import AutomationWorkflowModule
from assistant_modules.communication import MultimodalBridge, TextInterface, VoiceInterface
from assistant_modules.core_engine import RexReasoningEngine, SpanishNLPProcessor, UserMemoryManager
from assistant_modules.electronics import ElectronicsModule
from assistant_modules.integrations import IntegrationsHub
from assistant_modules.mathematics import MathematicsModule
from assistant_modules.mechatronics import MechatronicsModule
from assistant_modules.persistence import PersistenceStore
from assistant_modules.security_control import SecurityControlModule
from assistant_modules.software_systems import SoftwareSystemsModule
from assistant_modules.telecommunications import TelecommunicationsModule


@dataclass
class BackendResponse:
    intent: str
    action: str
    data: Dict[str, Any]


class RexAssistantBackend:
    """Fachada backend: núcleo IA + módulos de ingeniería + seguridad + persistencia."""

    def __init__(self, base_dir: Path | None = None) -> None:
        root = base_dir or Path.cwd()
        self.store = PersistenceStore(root / "memory" / "modular_backend")
        self.memory = UserMemoryManager(root / "memory" / "modular_backend" / "user_memory.json")

        self.nlp = SpanishNLPProcessor()
        self.reasoning = RexReasoningEngine()

        self.text = TextInterface()
        self.voice = VoiceInterface()
        self.multimodal = MultimodalBridge()

        self.electronics = ElectronicsModule()
        self.software = SoftwareSystemsModule()
        self.mechatronics = MechatronicsModule()
        self.telecom = TelecommunicationsModule()
        self.math = MathematicsModule()
        self.automation = AutomationWorkflowModule()
        self.security = SecurityControlModule()
        self.integrations = IntegrationsHub()

    def process_text(self, user_text: str, channel: str = "console") -> BackendResponse:
        message = self.text.receive(user_text, channel=channel)
        nlp_result = self.nlp.process(message.content)
        reasoning = self.reasoning.infer(nlp_result.normalized_text)

        data: Dict[str, Any]
        if reasoning.action == "electronics.solve":
            data = {
                "example": self.electronics.ohm_law(voltage=12, resistance=6).__dict__,
                "note": "Módulo electrónico activo",
            }
        elif reasoning.action == "software.solve":
            snippet = self.software.generate_code("python", "ordenar lista")
            data = {"snippet": snippet.__dict__}
        elif reasoning.action == "mechatronics.solve":
            data = {
                "torque_example": self.mechatronics.torque(10, 0.2),
                "power_example": self.mechatronics.mechanical_power(2.0, 1500),
            }
        else:
            data = {
                "reply": "Consulta recibida. Puedes pedir cálculos de electrónica, software, mecatrónica, telecom o matemáticas.",
            }

        self.store.append_log(f"intent={reasoning.intent}|action={reasoning.action}|text={nlp_result.normalized_text}")
        return BackendResponse(intent=reasoning.intent, action=reasoning.action, data=data)

    def architecture_summary(self) -> Dict[str, Any]:
        return {
            "frontend": ["console", "vscode", "web", "voice"],
            "backend": [
                "core_engine", "electronics", "software_systems", "mechatronics",
                "telecommunications", "mathematics", "automation_workflow", "security_control",
            ],
            "integrations": [i.name for i in self.integrations.list() if i.available],
            "persistence": [str(self.store.config_file), str(self.store.memory_file), str(self.store.log_file)],
        }
