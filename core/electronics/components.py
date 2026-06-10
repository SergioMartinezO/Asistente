from dataclasses import dataclass
from typing import Optional

class ComponentOverloadError(ValueError):
    """Excepción lanzada cuando un componente opera fuera de sus límites seguros (SOA)."""
    pass

@dataclass(frozen=True)
class Resistencia:
    """Modelado físico inmutable de un resistor comercial."""
    valor: float
    potencia_nominal: float = 0.25
    tolerancia: float = 5.0
    voltaje_max: Optional[float] = None

    def __post_init__(self) -> None:
        if self.valor <= 0:
            raise ValueError("La resistencia debe ser mayor que cero.")
        if self.potencia_nominal <= 0:
            raise ValueError("La potencia nominal debe ser positiva.")

    def validar_seguridad(self, voltaje_operacion: float, factor_seguridad: float = 1.5) -> None:
        """Valida que la disipación térmica sea segura. Lanza ComponentOverloadError en sobrecarga."""
        p_disipada = (voltaje_operacion ** 2) / self.valor
        if (p_disipada * factor_seguridad) > self.potencia_nominal:
            raise ComponentOverloadError(
                f"Sobrecarga térmica crítica: Se disiparán {p_disipada:.4f}W "
                f"en un componente de potencia nominal {self.potencia_nominal}W "
                f"bajo un factor de seguridad del {factor_seguridad}x."
            )


@dataclass(frozen=True)
class Capacitor:
    """Modelado físico inmutable de un capacitor comercial."""
    valor: float
    voltaje_nominal: float
    corriente_fuga: float = 1e-9

    def __post_init__(self) -> None:
        if self.valor <= 0:
            raise ValueError("La capacitancia debe ser positiva.")
        if self.voltaje_nominal <= 0:
            raise ValueError("El voltaje nominal debe ser positivo.")

    def validar_seguridad(self, voltaje_operacion: float) -> None:
        """Lanza ComponentOverloadError si se excede la rigidez dieléctrica."""
        if voltaje_operacion > self.voltaje_nominal:
            raise ComponentOverloadError(
                f"Ruptura dieléctrica inminente: Voltaje aplicado ({voltaje_operacion}V) "
                f"excede el límite del componente ({self.voltaje_nominal}V)."
            )

    def calcular_energia_almacenada(self, voltaje_aplicado: float) -> float:
        """Calcula la energía almacenada en Joules (J)."""
        self.validar_seguridad(voltaje_aplicado)
        return 0.5 * self.valor * (voltaje_aplicado ** 2)


@dataclass(frozen=True)
class Inductor:
    """Modelado físico inmutable de un inductor comercial."""
    valor: float
    corriente_saturacion: float
    resistencia_cobre: float = 0.1

    def __post_init__(self) -> None:
        if self.valor <= 0:
            raise ValueError("La inductancia debe ser positiva.")
        if self.corriente_saturacion <= 0:
            raise ValueError("La corriente de saturación debe ser positiva.")

    def validar_seguridad(self, corriente_operacion: float) -> None:
        """Lanza ComponentOverloadError si la corriente supera el punto de saturación."""
        if corriente_operacion > self.corriente_saturacion:
            raise ComponentOverloadError(
                f"Saturación del núcleo magnético: Corriente ({corriente_operacion}A) "
                f"supera el límite de saturación ({self.corriente_saturacion}A)."
            )

    def calcular_energia_almacenada(self, corriente_aplicada: float) -> float:
        """Calcula la energía almacenada en Joules (J)."""
        self.validar_seguridad(corriente_aplicada)
        return 0.5 * self.valor * (corriente_aplicada ** 2)
