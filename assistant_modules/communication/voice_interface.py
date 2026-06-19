from __future__ import annotations

from dataclasses import dataclass


@dataclass
class VoiceConfig:
    locale: str = "es-ES"
    tts_voice: str = "default"


class VoiceInterface:
    """Puente STT/TTS desacoplado (preparado para conectar proveedores reales)."""

    def __init__(self, config: VoiceConfig | None = None) -> None:
        self.config = config or VoiceConfig()

    def speech_to_text(self, audio_bytes: bytes) -> str:
        # Stub seguro: en producción conectar Whisper, Vosk o API Cloud.
        if not audio_bytes:
            return ""
        return "[transcripción simulada en español]"

    def text_to_speech(self, text: str) -> bytes:
        # Stub seguro: devolver bytes representativos; integración real en etapa siguiente.
        return text.encode("utf-8")
