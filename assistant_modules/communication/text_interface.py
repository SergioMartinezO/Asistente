from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class TextMessage:
    channel: str
    content: str


class TextInterface:
    """Interfaz de texto unificada (consola, vscode, web)."""

    def __init__(self) -> None:
        self.last_message: Optional[TextMessage] = None

    def receive(self, text: str, channel: str = "console") -> TextMessage:
        msg = TextMessage(channel=channel, content=text)
        self.last_message = msg
        return msg

    def send(self, text: str, channel: str = "console") -> TextMessage:
        msg = TextMessage(channel=channel, content=text)
        self.last_message = msg
        return msg
