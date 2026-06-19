from __future__ import annotations

from dataclasses import dataclass


@dataclass
class IntegrationStatus:
    name: str
    available: bool
    notes: str


class IntegrationsHub:
    """Registro simple de integraciones externas (IDE, simuladores, nube, hardware)."""

    def __init__(self) -> None:
        self._integrations = {
            "vscode": IntegrationStatus("vscode", True, "Integración por extensión y terminal"),
            "matlab": IntegrationStatus("matlab", True, "Soporte mediante actions/matlab_link.py"),
            "simulink": IntegrationStatus("simulink", True, "A través de MATLAB"),
            "github": IntegrationStatus("github", True, "Disponible por API/herramientas"),
            "onedrive": IntegrationStatus("onedrive", True, "Disponible por ruta sincronizada"),
            "arduino": IntegrationStatus("arduino", True, "Comunicación serial/USB"),
            "plc": IntegrationStatus("plc", True, "Modbus/TCP sugerido"),
        }

    def list(self) -> list[IntegrationStatus]:
        return list(self._integrations.values())

    def get(self, name: str) -> IntegrationStatus | None:
        return self._integrations.get(name.lower())
