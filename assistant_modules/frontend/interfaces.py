from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FrontendInterfaces:
    """Descriptor de arquitectura de frontend (chat, voz, consola/web)."""

    text_chat: bool = True
    voice: bool = True
    web: bool = True
    vscode: bool = True
