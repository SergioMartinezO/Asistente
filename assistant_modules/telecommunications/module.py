from __future__ import annotations

import math


class TelecommunicationsModule:
    """Funciones básicas de telecomunicaciones y señales."""

    @staticmethod
    def nyquist_rate(bandwidth_hz: float) -> float:
        return 2 * bandwidth_hz

    @staticmethod
    def shannon_capacity(bandwidth_hz: float, snr_linear: float) -> float:
        if bandwidth_hz <= 0 or snr_linear < 0:
            raise ValueError("Parámetros inválidos")
        return bandwidth_hz * math.log2(1 + snr_linear)

    @staticmethod
    def fspl_db(distance_km: float, frequency_mhz: float) -> float:
        if distance_km <= 0 or frequency_mhz <= 0:
            raise ValueError("distance_km y frequency_mhz deben ser > 0")
        return 32.44 + 20 * math.log10(distance_km) + 20 * math.log10(frequency_mhz)

    @staticmethod
    def protocol_reference() -> dict:
        return {
            "tcp_ip": "Transporte confiable y enrutamiento IP",
            "udp": "Baja latencia, sin garantía de entrega",
            "wifi": "IEEE 802.11",
            "bluetooth": "Enlace corto alcance, bajo consumo",
        }

    @staticmethod
    def modulation_hint(modulation: str) -> str:
        m = modulation.lower()
        if m in {"am", "fm", "pm"}:
            return f"{modulation.upper()}: modulación analógica clásica."
        return f"{modulation.upper()}: evaluar BER, ancho de banda y robustez al ruido."
