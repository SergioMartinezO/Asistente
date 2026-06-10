from typing import Dict, Any, Optional, Callable
from actions.base import BaseAction
from core.electronics.components import ComponentOverloadError
from core.electronics.calculations import calcular_ohm, calcular_divisor_tension

class ElectronicsAction(BaseAction):
    """Acción puente del framework para interactuar con el motor de electrónica core/electronics/."""

    @property
    def name(self) -> str:
        return "electronics"

    @property
    def description(self) -> str:
        return (
            "Resuelve circuitos de ingeniería, ley de ohm, divisores de tensión "
            "y evalúa la SOA térmica de componentes."
        )

    def sugerir_encapsulado(self, potencia_calculada: float) -> str:
        p_req = potencia_calculada * 1.5
        if p_req <= 0.125: return "Axial / SMD 0805 (1/8W)"
        if p_req <= 0.25:  return "Axial / SMD 1206 (1/4W)"
        if p_req <= 0.5:   return "Axial / SMD 2010 (1/2W)"
        if p_req <= 1.0:   return "Axial 1W"
        return "Cerámico / Cemento de Alta Potencia"

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

        try:
            if action == "ohm":
                v = parameters.get("voltage")
                i = parameters.get("current")
                r = parameters.get("resistance")
                res = calcular_ohm(
                    v=float(v) if v is not None else None,
                    i=float(i) if i is not None else None,
                    r=float(r) if r is not None else None
                )
                if "r_ideal" in res:
                    enc = self.sugerir_encapsulado(res["potencia"])
                    result = (
                        f"R Ideal = {res['r_ideal']:.2f} Ω | R Comercial = {res['r_comercial']:.1f} Ω\n"
                        f"Potencia = {res['potencia']:.4f} W | Encapsulado seguro = {enc}"
                    )
                else:
                    result = f"Resultado = {res} | Potencia = {res.get('potencia', 0.0):.4f}W"
                say(result)
                return result

            elif action == "divisor_tension":
                vin = float(parameters.get("vin", 0))
                r1 = float(parameters.get("r1", 0))
                r2 = float(parameters.get("r2", 0))
                res = calcular_divisor_tension(vin, r1, r2)
                result = (
                    f"Vout Ideal = {res['vout_ideal']:.4f} V | Vout Real = {res['vout_comercial']:.4f} V\n"
                    f"R1 Comercial ({res['r1_com'].serie}): {res['r1_com'].valor:.1f} Ω (P: {res['p_r1']:.4f}W)\n"
                    f"R2 Comercial ({res['r2_com'].serie}): {res['r2_com'].valor:.1f} Ω (P: {res['p_r2']:.4f}W)"
                )
                say(result)
                return result
            else:
                return f"Acción '{action}' no soportada."

        except ComponentOverloadError as err:
            err_msg = f"¡ALERTA DE SEGURIDAD FÍSICA! {str(err)}"
            say(err_msg)
            return err_msg
        except Exception as e:
            err_msg = f"Error en cálculo de ingeniería: {str(e)}"
            say(err_msg)
            return err_msg

def electronics(parameters: dict, player=None, speak=None):
    import asyncio
    return asyncio.run(ElectronicsAction().execute(parameters, player, speak))