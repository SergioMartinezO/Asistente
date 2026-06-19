from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class OhmResult:
    voltage: float
    current: float
    resistance: float


class ElectronicsModule:
    """Herramientas base de ingeniería electrónica."""

    @staticmethod
    def ohm_law(voltage: float | None = None, current: float | None = None, resistance: float | None = None) -> OhmResult:
        known = [v is not None for v in (voltage, current, resistance)].count(True)
        if known != 2:
            raise ValueError("Debe proporcionar exactamente dos parámetros de Ley de Ohm")

        if voltage is None:
            voltage = current * resistance
        elif current is None:
            current = voltage / resistance
        elif resistance is None:
            resistance = voltage / current

        return OhmResult(voltage=float(voltage), current=float(current), resistance=float(resistance))

    @staticmethod
    def rc_cutoff_frequency(resistance: float, capacitance: float) -> float:
        return 1.0 / (2.0 * math.pi * resistance * capacitance)

    @staticmethod
    def dbm_to_mw(dbm: float) -> float:
        return 10 ** (dbm / 10.0)

    @staticmethod
    def mw_to_dbm(mw: float) -> float:
        if mw <= 0:
            raise ValueError("mW debe ser > 0")
        return 10.0 * math.log10(mw)

    @staticmethod
    def vrms_to_vpp(vrms: float) -> float:
        return 2 * math.sqrt(2) * vrms

    @staticmethod
    def vpp_to_vrms(vpp: float) -> float:
        return vpp / (2 * math.sqrt(2))

    @staticmethod
    def nodal_solver_2x2(a11: float, a12: float, b1: float, a21: float, a22: float, b2: float) -> tuple[float, float]:
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-12:
            raise ValueError("Sistema singular en análisis nodal")
        v1 = (b1 * a22 - a12 * b2) / det
        v2 = (a11 * b2 - b1 * a21) / det
        return v1, v2

    @staticmethod
    def mesh_solver_2x2(z11: float, z12: float, v1: float, z21: float, z22: float, v2: float) -> tuple[float, float]:
        # Mismo método lineal para corrientes de malla I1, I2
        det = z11 * z22 - z12 * z21
        if abs(det) < 1e-12:
            raise ValueError("Sistema singular en análisis de mallas")
        i1 = (v1 * z22 - z12 * v2) / det
        i2 = (z11 * v2 - v1 * z21) / det
        return i1, i2

    @staticmethod
    def datasheet_hint(component: str) -> str:
        return f"Usa búsqueda técnica: 'datasheet {component} filetype:pdf'"

    @staticmethod
    def basic_simulation_voltage_divider(vin: float, r1: float, r2: float) -> float:
        if r1 <= 0 or r2 <= 0:
            raise ValueError("Resistencias deben ser > 0")
        return vin * (r2 / (r1 + r2))
