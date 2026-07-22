from typing import Dict, Any, Optional, Callable
from actions.base import BaseAction
from core.electronics.components import ComponentOverloadError
from core.electronics.calculations import (
    calcular_ohm,
    calcular_divisor_tension,
    calcular_serie,
    calcular_paralelo,
    calcular_reactancia_c,
    calcular_reactancia_l,
    calcular_frecuencia_corte,
    convertir_dbm_mw,
    convertir_vrms_vpp,
    decodificar_color_resistencia,
    convertir_prefijo_si,
)

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
                rl = parameters.get("rl")
                rl_val = float(rl) if rl is not None else None
                res = calcular_divisor_tension(vin, r1, r2, rl_val)
                result = (
                    f"Vout Ideal = {res['vout_ideal']:.4f} V | Vout Real = {res['vout_comercial']:.4f} V\n"
                    f"R1 Comercial ({res['r1_com'].serie}): {res['r1_com'].valor:.1f} Ω (P: {res['p_r1']:.4f}W)\n"
                    f"R2 Comercial ({res['r2_com'].serie}): {res['r2_com'].valor:.1f} Ω (P: {res['p_r2']:.4f}W)"
                )
                say(result)
                return result

            elif action == "serie":
                values = [float(v) for v in (parameters.get("values") or [])]
                res = calcular_serie(values)
                result = f"Resistencia equivalente en serie = {res['equivalente']:.2f} Ω ({res['n']} resistencias)"
                say(result)
                return result

            elif action == "paralelo":
                values = [float(v) for v in (parameters.get("values") or [])]
                res = calcular_paralelo(values)
                result = f"Resistencia equivalente en paralelo = {res['equivalente']:.2f} Ω ({res['n']} resistencias)"
                say(result)
                return result

            elif action == "reactancia_c":
                f = float(parameters.get("frequency"))
                c = float(parameters.get("capacitance"))
                res = calcular_reactancia_c(f, c)
                result = f"Reactancia capacitiva Xc = {res['reactancia']:.4f} Ω"
                say(result)
                return result

            elif action == "reactancia_l":
                f = float(parameters.get("frequency"))
                l = float(parameters.get("inductance"))
                res = calcular_reactancia_l(f, l)
                result = f"Reactancia inductiva Xl = {res['reactancia']:.4f} Ω"
                say(result)
                return result

            elif action == "frecuencia_corte":
                r = float(parameters.get("resistance"))
                c = parameters.get("capacitance")
                l = parameters.get("inductance")
                res = calcular_frecuencia_corte(
                    r,
                    float(c) if c is not None else None,
                    float(l) if l is not None else None,
                )
                result = f"Frecuencia de corte ({res['circuito']}) = {res['frecuencia_corte']:.4f} Hz"
                say(result)
                return result

            elif action == "dbm_mw":
                dbm = parameters.get("dbm")
                mw = parameters.get("mw")
                res = convertir_dbm_mw(
                    float(dbm) if dbm is not None else None,
                    float(mw) if mw is not None else None,
                )
                result = f"{res['dbm']:.4f} dBm = {res['mw']:.6f} mW"
                say(result)
                return result

            elif action == "vrms_vpp":
                vrms = parameters.get("vrms")
                vpp = parameters.get("vpp")
                res = convertir_vrms_vpp(
                    float(vrms) if vrms is not None else None,
                    float(vpp) if vpp is not None else None,
                )
                result = f"Vrms = {res['vrms']:.4f} V | Vpp = {res['vpp']:.4f} V"
                say(result)
                return result

            elif action == "codigo_colores":
                bands = parameters.get("bands") or []
                res = decodificar_color_resistencia(bands)
                result = f"Valor = {res['valor']:.0f} Ω | Tolerancia = ±{res['tolerancia_pct']:.2f}%"
                say(result)
                return result

            elif action == "prefijo_si":
                value = float(parameters.get("value"))
                from_prefix = parameters.get("from_prefix", "base")
                to_prefix = parameters.get("to_prefix", "base")
                res = convertir_prefijo_si(value, from_prefix, to_prefix)
                result = f"{value} {from_prefix} = {res['resultado']:g} {to_prefix}"
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