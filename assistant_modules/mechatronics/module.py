from __future__ import annotations

import math


class MechatronicsModule:
    """Cálculos y utilidades de mecatrónica."""

    @staticmethod
    def torque(force_n: float, lever_arm_m: float) -> float:
        return force_n * lever_arm_m

    @staticmethod
    def mechanical_power(torque_nm: float, rpm: float) -> float:
        omega = 2 * math.pi * (rpm / 60.0)
        return torque_nm * omega

    @staticmethod
    def gear_ratio(driver_teeth: int, driven_teeth: int) -> float:
        if driver_teeth <= 0:
            raise ValueError("driver_teeth debe ser > 0")
        return driven_teeth / driver_teeth

    @staticmethod
    def motor_control_hint(motor_type: str) -> str:
        mt = motor_type.lower()
        if "servo" in mt:
            return "Control PWM (50Hz), ancho de pulso típico 1-2 ms."
        if "paso" in mt or "step" in mt:
            return "Usar driver dedicado (A4988/DRV8825), control STEP/DIR."
        return "Motor DC: control con puente H + PWM + realimentación opcional."

    @staticmethod
    def hardware_link_hint() -> dict:
        return {
            "arduino": "Serial/USB listo",
            "plc": "Modbus/TCP sugerido",
            "microcontroladores": "UART/SPI/I2C según plataforma",
        }
