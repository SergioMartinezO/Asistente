import math
from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable, List
from actions.base import BaseAction

# ──────────────────────────────────────────────────────────────────────
# Fundamento Teórico y Matemático: Normalización de Componentes (Series E)
#
# Las series de valores preferidos (como E24 y E96) se basan en una progresión
# geométrica propuesta por Charles Renard y normalizada bajo la IEC 60063.
# La fórmula para la progresión geométrica es:
#
#   V_n = 10^(n / N)
#
# Donde N representa la serie (ej. 24 o 96) y n es el índice entero en el
# intervalo [0, N-1].
#
# En E24 (tolerancia ±5%), cada década se divide en 24 pasos:
#   10^(n/24) redondeado a 2 dígitos significativos.
# En E96 (tolerancia ±1%), cada década se divide en 96 pasos:
#   10^(n/96) redondeado a 3 dígitos significativos.
# ──────────────────────────────────────────────────────────────────────

# Valores base normalizados de la serie E24 (2 dígitos de precisión)
E24_BASE: List[float] = [
    1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0,
    3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1
]

# Valores base normalizados de la serie E96 (3 dígitos de precisión)
E96_BASE: List[float] = [
    1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30,
    1.33, 1.37, 1.40, 1.43, 1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74,
    1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10, 2.15, 2.21, 2.26, 2.32,
    2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
    3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12,
    4.22, 4.32, 4.42, 4.53, 4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49,
    5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65, 6.81, 6.98, 7.15, 7.32,
    7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76
]

@dataclass(frozen=True)
class Resistencia:
    valor_teorico: float
    valor_comercial: float
    serie: str
    error_relativo: float
    potencia_disipada: float = 0.0
    potencia_nominal_sugerida: float = 0.0
    encapsulado_sugerido: str = "N/A"

@dataclass(frozen=True)
class Impedancia:
    resistencia: float
    reactancia: float
    modulo: float
    angulo_rad: float

class ElectronicsAction(BaseAction):
    """Acción especializada en cálculos de ingeniería electrónica y normalización de componentes."""

    # Encapsulados comerciales de resistencias de agujero pasante (Through-Hole) y SMD comunes por potencia nominal
    ENCAPSULADOS_COMERCIALES: List[Dict[str, Any]] = [
        {"max_p": 0.0625, "nombre": "SMD 0201 (1/16W)"},
        {"max_p": 0.1,    "nombre": "SMD 0402 (1/10W)"},
        {"max_p": 0.125,  "nombre": "Through-Hole Axial / SMD 0805 (1/8W)"},
        {"max_p": 0.25,   "nombre": "Through-Hole Axial / SMD 1206 (1/4W)"},
        {"max_p": 0.5,    "nombre": "Through-Hole Axial / SMD 2010 (1/2W)"},
        {"max_p": 1.0,    "nombre": "Through-Hole Axial 1W"},
        {"max_p": 2.0,    "nombre": "Through-Hole Axial 2W"},
        {"max_p": 5.0,    "nombre": "Cerámico de Cemento 5W"},
    ]

    @property
    def name(self) -> str:
        return "electronics"

    @property
    def description(self) -> str:
        return (
            "Permite resolver problemas de Ley de Ohm, calcular divisores de tensión, "
            "frecuencias de corte RC/RL, reactancias y encontrar valores comerciales "
            "normalizados en las series E24 (5%) y E96 (1%)."
        )

    def sugerir_encapsulado(self, potencia_calculada: float, factor_seguridad: float = 1.5) -> Dict[str, Any]:
        """Selecciona el encapsulado comercial óptimo basándose en la potencia disipada y derating térmico.

        Args:
            potencia_calculada: Potencia eléctrica real disipada por el componente en Watts (W).
            factor_seguridad: Factor multiplicador para garantizar confiabilidad (por defecto 1.5x).

        Returns:
            Dict: Diccionario con la potencia nominal sugerida y el nombre del encapsulado comercial.
        """
        p_segura = potencia_calculada * factor_seguridad
        for enc in self.ENCAPSULADOS_COMERCIALES:
            if enc["max_p"] >= p_segura:
                return {"potencia_nominal": enc["max_p"], "nombre": enc["nombre"]}
        return {"potencia_nominal": p_segura, "nombre": "Especial / Potencia Requerida por Disipador"}

    def buscar_comercial(self, valor: float, usar_e96: bool = False, potencia_calc: float = 0.0) -> Resistencia:
        """Encuentra el valor comercial más cercano de la serie E24 o E96 para un valor teórico.

        Utiliza el algoritmo de búsqueda binaria (bisect_left) para localizar el elemento
        más cercano en la progresión logarítmica con complejidad temporal O(log N).

        Args:
            valor: El valor de resistencia teórico en Ohmios (Ω).
            usar_e96: Verdadero para usar la serie E96 (1%), Falso para E24 (5%).
            potencia_calc: Potencia disipada real en Watts (W).

        Returns:
            Resistencia: Un objeto con el valor teórico, comercial aproximado, error y potencia.
        """
        import bisect

        if valor <= 0:
            return Resistencia(valor, 0.0, "N/A", 0.0)

        exponente = math.floor(math.log10(valor))
        mantisa = valor / (10 ** exponente)

        serie_nombre = "E96" if usar_e96 else "E24"
        base = E96_BASE if usar_e96 else E24_BASE

        # Búsqueda binaria de la posición de la mantisa en la serie normalizada
        idx = bisect.bisect_left(base, mantisa)

        # Evaluar candidatos adyacentes
        if idx == 0:
            cercano = base[0]
        elif idx == len(base):
            cercano = base[-1]
        else:
            izq = base[idx - 1]
            der = base[idx]
            cercano = izq if abs(izq - mantisa) < abs(der - mantisa) else der

        valor_comercial = cercano * (10 ** exponente)
        error = abs(valor_comercial - valor) / valor * 100

        # Sugerir encapsulado comercial
        sug = self.sugerir_encapsulado(potencia_calc)

        return Resistencia(
            valor_teorico=valor,
            valor_comercial=valor_comercial,
            serie=serie_nombre,
            error_relativo=error,
            potencia_disipada=potencia_calc,
            potencia_nominal_sugerida=sug["potencia_nominal"],
            encapsulado_sugerido=sug["nombre"]
        )

    async def execute(
        self,
        parameters: Dict[str, Any],
        player: Optional[Any] = None,
        speak_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        action = parameters.get("action", "").lower()

        def log(msg: str) -> None:
            if player and hasattr(player, "write_log"):
                player.write_log(f"ELEC: {msg}")

        def say(msg: str) -> None:
            log(msg)
            if speak_callback:
                speak_callback(msg)

        # ── LEY DE OHM ──
        if action == "ohm":
            v = parameters.get("voltage")
            i = parameters.get("current")
            r = parameters.get("resistance")
            p = parameters.get("power")
            results = []

            if v is not None and i is not None:
                r_val = float(v) / float(i)
                p_val = float(v) * float(i)
                res_com = self.buscar_comercial(r_val, potencia_calc=p_val)
                results = [
                    f"Resistencia teórica: {r_val:.4f} Ω",
                    f"Comercial (E24): {res_com.valor_comercial:.1f} Ω (Error: {res_com.error_relativo:.2f}%)",
                    f"Potencia: {p_val:.4f} W",
                    f"Encapsulado comercial sugerido: {res_com.encapsulado_sugerido}"
                ]
            elif v is not None and r is not None:
                i_val = float(v) / float(r)
                p_val = (float(v) ** 2) / float(r)
                res_com = self.buscar_comercial(float(r), potencia_calc=p_val)
                results = [
                    f"Corriente: {i_val:.4f} A",
                    f"Potencia: {p_val:.4f} W",
                    f"Encapsulado comercial sugerido: {res_com.encapsulado_sugerido}"
                ]
            elif i is not None and r is not None:
                v_val = float(i) * float(r)
                p_val = (float(i) ** 2) * float(r)
                res_com = self.buscar_comercial(float(r), potencia_calc=p_val)
                results = [
                    f"Voltaje: {v_val:.4f} V",
                    f"Potencia: {p_val:.4f} W",
                    f"Encapsulado comercial sugerido: {res_com.encapsulado_sugerido}"
                ]
            else:
                msg = "Sir, necesito al menos dos valores válidos para la Ley de Ohm."
                say(msg)
                return msg

            res_str = " | ".join(results)
            say(res_str)
            return res_str

        # ── DIVISOR DE TENSIÓN ──
        elif action == "divisor_tension":
            vin = float(parameters.get("vin", 0))
            r1 = float(parameters.get("r1", 0))
            r2 = float(parameters.get("r2", 0))
            if (r1 + r2) == 0:
                return "Error: Divisor por cero en R1 + R2."

            vout = vin * r2 / (r1 + r2)
            
            # Análisis térmico para divisor de tensión
            # Corriente del lazo: I = Vin / (R1 + R2)
            i_lazo = vin / (r1 + r2)
            p_r1 = (i_lazo ** 2) * r1
            p_r2 = (i_lazo ** 2) * r2

            # Encontrar contrapartes comerciales con su respectivo análisis térmico
            r1_com = self.buscar_comercial(r1, potencia_calc=p_r1)
            r2_com = self.buscar_comercial(r2, potencia_calc=p_r2)
            vout_com = vin * r2_com.valor_comercial / (r1_com.valor_comercial + r2_com.valor_comercial)

            result = (
                f"Vout Teórico = {vout:.4f} V | Vout Real (E24) = {vout_com:.4f} V\n"
                f"R1 Comercial: {r1_com.valor_comercial:.1f} Ω (Error: {r1_com.error_relativo:.2f}%, P_disipada: {p_r1:.4f}W, Sugerido: {r1_com.encapsulado_sugerido})\n"
                f"R2 Comercial: {r2_com.valor_comercial:.1f} Ω (Error: {r2_com.error_relativo:.2f}%, P_disipada: {p_r2:.4f}W, Sugerido: {r2_com.encapsulado_sugerido})"
            )
            say(result)
            return result

        # ── FRECUENCIA DE CORTE (RC / RL) ──
        elif action == "frecuencia_corte":
            r = float(parameters.get("resistance", 0))
            c = parameters.get("capacitance")
            l = parameters.get("inductance")

            if c is not None:
                c_val = float(c)
                fc = 1 / (2 * math.pi * r * c_val)
                result = f"Frecuencia de corte RC: fc = {fc:.4f} Hz (R={r} Ω, C={c_val} F)"
            elif l is not None:
                l_val = float(l)
                fc = r / (2 * math.pi * l_val)
                result = f"Frecuencia de corte RL: fc = {fc:.4f} Hz (R={r} Ω, L={l_val} H)"
            else:
                result = "Sir, proporcione R y C, o R y L."

            say(result)
            return result

        # ── CÓDIGO DE COLORES ──
        elif action == "codigo_colores":
            colores = {
                "negro": 0, "marrón": 1, "rojo": 2, "naranja": 3, "amarillo": 4,
                "verde": 5, "azul": 6, "violeta": 7, "gris": 8, "blanco": 9
            }
            tolerancias = {
                "dorado": "±5%", "plateado": "±10%", "marrón": "±1%", "rojo": "±2%"
            }
            bandas = parameters.get("bands", [])
            if len(bandas) < 3:
                msg = "Sir, necesito al menos 3 bandas de colores para calcular la resistencia."
                say(msg)
                return msg

            bandas = [b.lower() for b in bandas]
            try:
                if len(bandas) == 4:
                    val = (colores[bandas[0]] * 10 + colores[bandas[1]]) * (10 ** colores[bandas[2]])
                    tol = tolerancias.get(bandas[3], "±20%")
                else:
                    val = (colores[bandas[0]] * 100 + colores[bandas[1]] * 10 + colores[bandas[2]]) * (10 ** colores[bandas[3]])
                    tol = tolerancias.get(bandas[4], "±20%")

                if val >= 1_000_000:
                    display = f"{val/1_000_000:.2f} MΩ"
                elif val >= 1_000:
                    display = f"{val/1_000:.2f} kΩ"
                else:
                    display = f"{val} Ω"

                res_com = self.buscar_comercial(val)
                result = (
                    f"Resistencia Leída: {display} {tol}\n"
                    f"Aproximación Comercial Cercana (E24): {res_com.valor_comercial:.1f} Ω (Error: {res_com.error_relativo:.2f}%)"
                )
            except KeyError as e:
                result = f"Color no reconocido: {e}"

            say(result)
            return result

        else:
            msg = f"Acción electrónica '{action}' no soportada por el Framework actualmente."
            say(msg)
            return msg

# Shim para compatibilidad con código existente
def electronics(parameters: dict, player=None, speak=None):
    import asyncio
    action_instance = ElectronicsAction()
    return asyncio.run(action_instance.execute(parameters, player, speak))