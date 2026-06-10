import math
from typing import Dict, Any, Optional, Callable
from actions.base import BaseAction
from core.components import Resistencia, Capacitor, Inductor
from core.commercial import buscar_resistencia_comercial

class ElectronicsAction(BaseAction):
    """Acción que expone el motor de cálculos de ingeniería electrónica del core al asistente."""

    @property
    def name(self) -> str:
        return "electronics"

    @property
    def description(self) -> str:
        return (
            "Resuelve Ley de Ohm, divisores de tensión e impedancias con análisis físico "
            "y selección de encapsulados comerciales en las series E24/E96."
        )

    def sugerir_encapsulado(self, potencia_calculada: float, factor_seguridad: float = 1.5) -> str:
        """Determina el encapsulado comercial seguro basado en la disipación real."""
        p_requerida = potencia_calculada * factor_seguridad
        if p_requerida <= 0.0625: return "SMD 0201 (1/16W)"
        if p_requerida <= 0.1:    return "SMD 0402 (1/10W)"
        if p_requerida <= 0.125:  return "Through-Hole Axial / SMD 0805 (1/8W)"
        if p_requerida <= 0.25:   return "Through-Hole Axial / SMD 1206 (1/4W)"
        if p_requerida <= 0.5:    return "Through-Hole Axial / SMD 2010 (1/2W)"
        if p_requerida <= 1.0:    return "Through-Hole Axial 1W"
        if p_requerida <= 2.0:    return "Through-Hole Axial 2W"
        if p_requerida <= 5.0:    return "Cerámico de Cemento 5W"
        return "Disipador de potencia dedicado / encapsulado metálico"

    async def execute(
        self,
        parameters: Dict[str, Any],
        player: Optional[Any] = None,
        speak_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        action = parameters.get("action", "").lower()

        def say(msg: str) -> None:
            if player and hasattr(player, "write_log"):
                player.write_log(f"ELEC: {msg}")
            if speak_callback:
                speak_callback(msg)

        if action == "ohm":
            v = parameters.get("voltage")
            i = parameters.get("current")
            r = parameters.get("resistance")

            if v is not None and i is not None:
                r_teorica = float(v) / float(i)
                p_disipada = float(v) * float(i)
                res_com = buscar_resistencia_comercial(r_teorica)
                segura = res_com.validar_seguridad(float(v))
                enc = self.sugerir_encapsulado(p_disipada)
                result = (
                    f"Resistencia ideal: {r_teorica:.2f} Ω | Comercial E24: {res_com.valor:.1f} Ω\n"
                    f"Potencia Disipada: {p_disipada:.4f} W | Operación Segura: {segura}\n"
                    f"Encapsulado sugerido comercial: {enc}"
                )
            elif v is not None and r is not None:
                i_val = float(v) / float(r)
                p_disipada = (float(v) ** 2) / float(r)
                enc = self.sugerir_encapsulado(p_disipada)
                result = (
                    f"Corriente calculada: {i_val:.4f} A | Potencia Disipada: {p_disipada:.4f} W\n"
                    f"Encapsulado sugerido comercial para R: {enc}"
                )
            elif i is not None and r is not None:
                v_val = float(i) * float(r)
                p_disipada = (float(i) ** 2) * float(r)
                enc = self.sugerir_encapsulado(p_disipada)
                result = (
                    f"Voltaje resultante: {v_val:.4f} V | Potencia Disipada: {p_disipada:.4f} W\n"
                    f"Encapsulado sugerido comercial para R: {enc}"
                )
            else:
                result = "Sir, se requieren al menos dos variables físicas (voltage, current, resistance)."

            say(result)
            return result

        elif action == "divisor_tension":
            vin = float(parameters.get("vin", 0))
            r1 = float(parameters.get("r1", 0))
            r2 = float(parameters.get("r2", 0))

            if (r1 + r2) == 0:
                return "Error físico: División por cero en malla cerrada."

            i_lazo = vin / (r1 + r2)
            p_r1 = (i_lazo ** 2) * r1
            p_r2 = (i_lazo ** 2) * r2

            r1_com = buscar_resistencia_comercial(r1)
            r2_com = buscar_resistencia_comercial(r2)
            vout_com = vin * r2_com.valor / (r1_com.valor + r2_com.valor)

            enc_r1 = self.sugerir_encapsulado(p_r1)
            enc_r2 = self.sugerir_encapsulado(p_r2)

            result = (
                f"Vout Calculado = {vin * r2 / (r1 + r2):.4f} V | Vout Comercial = {vout_com:.4f} V\n"
                f"R1 Comercial ({r1_com.serie}): {r1_com.valor:.1f} Ω (P: {p_r1:.4f}W, {enc_r1})\n"
                f"R2 Comercial ({r2_com.serie}): {r2_com.valor:.1f} Ω (P: {p_r2:.4f}W, {enc_r2})"
            )
            say(result)
            return result

        else:
            result = f"Acción '{action}' no identificada."
            say(result)
            return result

def electronics(parameters: dict, player=None, speak=None):
    import asyncio
    return asyncio.run(ElectronicsAction().execute(parameters, player, speak))