from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class Resistencia:
    """Representa un resistor comercial con sus límites físicos de operación.
    
    Attributes:
        valor: Valor en ohmios (Ω).
        potencia_nominal: Potencia nominal máxima disipable en Watts (W).
        tolerancia: Tolerancia porcentual permitida (ej. 1 para ±1%, 5 para ±5%).
        voltaje_max: Voltaje máximo soportado por rigidez dieléctrica en Volts (V).
    """
    valor: float
    potencia_nominal: float = 0.25
    tolerancia: float = 5.0
    voltaje_max: Optional[float] = None

    def __post_init__(self) -> None:
        if self.valor <= 0:
            raise ValueError("El valor de resistencia debe ser estrictamente positivo.")
        if self.potencia_nominal <= 0:
            raise ValueError("La potencia nominal debe ser positiva.")

    def calcular_voltaje_max_fisico(self) -> float:
        """Determina el límite de voltaje antes de exceder la potencia nominal."""
        import math
        return math.sqrt(self.potencia_nominal * self.valor)

    def validar_seguridad(self, voltaje_operacion: float, factor_seguridad: float = 1.5) -> bool:
        """Determina si la resistencia opera bajo condiciones seguras.
        
        Args:
            voltaje_operacion: Voltaje continuo aplicado sobre la resistencia (V).
            factor_seguridad: Factor multiplicador para el margen de seguridad térmica (1.5x).
            
        Returns:
            bool: True si opera de forma segura dentro de los límites físicos, False en caso contrario.
        """
        potencia_disipada = (voltaje_operacion ** 2) / self.valor
        return (potencia_disipada * factor_seguridad) <= self.potencia_nominal


@dataclass(frozen=True)
class Capacitor:
    """Representa un capacitor comercial con sus especificaciones de seguridad.
    
    Attributes:
        valor: Capacitancia en Faradios (F).
        voltaje_nominal: Voltaje de ruptura dieléctrica nominal en Volts (V).
        corriente_fuga: Corriente parásita de fuga estimada en Amperios (A).
    """
    valor: float
    voltaje_nominal: float
    corriente_fuga: float = 1e-9

    def __post_init__(self) -> None:
        if self.valor <= 0:
            raise ValueError("El valor de capacitancia debe ser estrictamente positivo.")
        if self.voltaje_nominal <= 0:
            raise ValueError("El voltaje nominal de ruptura debe ser positivo.")

    def calcular_energia_almacenada(self, voltaje_aplicado: float) -> float:
        """Calcula la energía almacenada en el campo eléctrico en Joules (J)."""
        if voltaje_aplicado > self.voltaje_nominal:
            raise ValueError("Sobrecarga crítica: El voltaje supera el voltaje de ruptura dieléctrica.")
        return 0.5 * self.valor * (voltaje_aplicado ** 2)


@dataclass(frozen=True)
class Inductor:
    """Representa un inductor comercial y sus límites de saturación magnética.
    
    Attributes:
        valor: Inductancia en Henrios (H).
        corriente_saturacion: Corriente máxima antes de perder características del núcleo magnético (A).
        resistencia_cobre: Resistencia de serie equivalente de corriente continua (ESR/R_DC) en Ohmios (Ω).
    """
    valor: float
    corriente_saturacion: float
    resistencia_cobre: float = 0.1

    def __post_init__(self) -> None:
        if self.valor <= 0:
            raise ValueError("El valor de inductancia debe ser positivo.")
        if self.corriente_saturacion <= 0:
            raise ValueError("La corriente de saturación debe ser estrictamente positiva.")

    def calcular_energia_almacenada(self, corriente_aplicada: float) -> float:
        """Calcula la energía almacenada en el campo magnético en Joules (J)."""
        if corriente_aplicada > self.corriente_saturacion:
            raise ValueError("Saturación crítica: La corriente excede el límite magnético del núcleo.")
        return 0.5 * self.valor * (corriente_aplicada ** 2)
