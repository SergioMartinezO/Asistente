from __future__ import annotations

import cmath
import math
from typing import Iterable, List


class MathematicsModule:
    """Utilidades matemáticas de ingeniería."""

    @staticmethod
    def derivative_numerical(f, x: float, h: float = 1e-6) -> float:
        return (f(x + h) - f(x - h)) / (2 * h)

    @staticmethod
    def integral_trapezoidal(xs: Iterable[float], ys: Iterable[float]) -> float:
        x = list(xs)
        y = list(ys)
        if len(x) != len(y) or len(x) < 2:
            raise ValueError("Series inválidas")
        area = 0.0
        for i in range(len(x) - 1):
            area += (x[i + 1] - x[i]) * (y[i + 1] + y[i]) / 2.0
        return area

    @staticmethod
    def solve_2x2(a11: float, a12: float, b1: float, a21: float, a22: float, b2: float) -> tuple[float, float]:
        det = a11 * a22 - a12 * a21
        if abs(det) < 1e-12:
            raise ValueError("Sistema singular")
        x = (b1 * a22 - a12 * b2) / det
        y = (a11 * b2 - b1 * a21) / det
        return x, y

    @staticmethod
    def first_order_ode_step(y: float, t: float, dt: float, f) -> float:
        # Euler explícito
        return y + dt * f(t, y)

    @staticmethod
    def laplace_hint(function_desc: str) -> str:
        return f"Aplicar tabla de Laplace para: {function_desc}."

    @staticmethod
    def fourier_hint(signal_desc: str) -> str:
        return f"Analizar componentes frecuenciales de: {signal_desc}."

    @staticmethod
    def to_polar(z: complex) -> tuple[float, float]:
        return abs(z), math.degrees(cmath.phase(z))

    @staticmethod
    def to_rect(magnitude: float, angle_deg: float) -> complex:
        ang = math.radians(angle_deg)
        return magnitude * (math.cos(ang) + 1j * math.sin(ang))
