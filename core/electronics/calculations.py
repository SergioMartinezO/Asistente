import math
from core.electronics.components import Resistencia, ComponentOverloadError
from core.electronics.commercial import buscar_resistencia_comercial
from typing import Dict, Any, List, Optional

def calcular_ohm(v: float = None, i: float = None, r: float = None) -> Dict[str, Any]:
    """Resuelve la Ley de Ohm y valida la potencia disipada.
    
    Lanza ComponentOverloadError si la resistencia calculada o dada se sobrecarga.
    """
    if v is not None and i is not None:
        r_val = v / i
        p_val = v * i
        res = buscar_resistencia_comercial(r_val)
        res.validar_seguridad(v)
        return {"r_ideal": r_val, "r_comercial": res.valor, "potencia": p_val, "seguro": True, "encapsulado": res.potencia_nominal}
    elif v is not None and r is not None:
        i_val = v / r
        p_val = (v ** 2) / r
        res = Resistencia(valor=r)
        res.validar_seguridad(v)
        return {"i": i_val, "potencia": p_val, "seguro": True}
    elif i is not None and r is not None:
        v_val = i * r
        p_val = (i ** 2) * r
        res = Resistencia(valor=r)
        res.validar_seguridad(v_val)
        return {"v": v_val, "potencia": p_val, "seguro": True}
    else:
        raise ValueError("Se requieren al menos dos parámetros físicos.")

def calcular_divisor_tension(
    vin: float, 
    r1: float, 
    r2: float, 
    rl: Optional[float] = None
) -> Dict[str, Any]:
    """Calcula un divisor de tensión considerando el efecto de carga real (RL).
    
    Si RL no es provisto, se asume un circuito abierto (resistencia infinita).
    
    Lanza ComponentOverloadError si el aumento de corriente sobrecarga R1.
    """
    if (r1 + r2) == 0:
        raise ValueError("Divisor por cero en R1 + R2.")

    # Calcular resistencia equivalente del paralelo (R2 || RL)
    if rl is not None and rl > 0:
        r2_eq = (r2 * rl) / (r2 + rl)
    else:
        r2_eq = r2

    r_total = r1 + r2_eq
    if r_total == 0:
        raise ValueError("Resistencia equivalente total de la malla es cero.")

    # Corriente del lazo principal de entrada
    i_lazo = vin / r_total
    
    # Caída y potencia real disipada en R1
    p_r1 = (i_lazo ** 2) * r1
    
    # Tensión real de salida sobre R2 || RL
    vout = vin * r2_eq / r_total
    
    # Potencia real disipada en R2 (usando voltaje de salida sobre R2)
    p_r2 = (vout ** 2) / r2

    r1_com = buscar_resistencia_comercial(r1)
    r2_com = buscar_resistencia_comercial(r2)

    # Validar disipación bajo condiciones dinámicas reales del circuito
    # R1 ve la tensión de caída Vin - Vout
    r1_com.validar_seguridad(vin - vout)
    # R2 ve la tensión de salida directamente
    r2_com.validar_seguridad(vout)

    # Vout real con componentes comerciales aproximados
    if rl is not None and rl > 0:
        r2_com_eq = (r2_com.valor * rl) / (r2_com.valor + rl)
    else:
        r2_com_eq = r2_com.valor
    
    vout_com = vin * r2_com_eq / (r1_com.valor + r2_com_eq)

    return {
        "vout_ideal": vout,
        "vout_comercial": vout_com,
        "p_r1": p_r1,
        "p_r2": p_r2,
        "r1_com": r1_com,
        "r2_com": r2_com
    }


def calcular_serie(values: List[float]) -> Dict[str, Any]:
    """Resistencia equivalente de resistores en serie: Req = R1 + R2 + ... + Rn."""
    if not values or len(values) < 2:
        raise ValueError("Se requieren al menos dos resistencias.")
    total = sum(values)
    return {"equivalente": total, "n": len(values)}


def calcular_paralelo(values: List[float]) -> Dict[str, Any]:
    """Resistencia equivalente de resistores en paralelo: 1/Req = 1/R1 + 1/R2 + ... + 1/Rn."""
    if not values or len(values) < 2:
        raise ValueError("Se requieren al menos dos resistencias.")
    if any(v <= 0 for v in values):
        raise ValueError("Todas las resistencias deben ser mayores que cero.")
    inv_total = sum(1.0 / v for v in values)
    equivalente = 1.0 / inv_total
    return {"equivalente": equivalente, "n": len(values)}


def calcular_reactancia_c(frequency: float, capacitance: float) -> Dict[str, Any]:
    """Reactancia capacitiva: Xc = 1 / (2 * pi * f * C)."""
    if frequency is None or capacitance is None:
        raise ValueError("Se requieren frecuencia y capacitancia.")
    if frequency <= 0 or capacitance <= 0:
        raise ValueError("Frecuencia y capacitancia deben ser mayores que cero.")
    xc = 1.0 / (2 * math.pi * frequency * capacitance)
    return {"reactancia": xc, "tipo": "capacitiva"}


def calcular_reactancia_l(frequency: float, inductance: float) -> Dict[str, Any]:
    """Reactancia inductiva: Xl = 2 * pi * f * L."""
    if frequency is None or inductance is None:
        raise ValueError("Se requieren frecuencia e inductancia.")
    if frequency <= 0 or inductance <= 0:
        raise ValueError("Frecuencia e inductancia deben ser mayores que cero.")
    xl = 2 * math.pi * frequency * inductance
    return {"reactancia": xl, "tipo": "inductiva"}


def calcular_frecuencia_corte(
    resistance: float,
    capacitance: Optional[float] = None,
    inductance: Optional[float] = None,
) -> Dict[str, Any]:
    """Frecuencia de corte de un filtro de primer orden.

    RC: fc = 1 / (2 * pi * R * C). RL: fc = R / (2 * pi * L).
    Se elige el modo según qué parámetro (C o L) se proporcione.
    """
    if resistance is None or resistance <= 0:
        raise ValueError("Se requiere una resistencia mayor que cero.")
    if capacitance:
        fc = 1.0 / (2 * math.pi * resistance * capacitance)
        return {"frecuencia_corte": fc, "circuito": "RC"}
    if inductance:
        fc = resistance / (2 * math.pi * inductance)
        return {"frecuencia_corte": fc, "circuito": "RL"}
    raise ValueError("Se requiere capacitancia (circuito RC) o inductancia (circuito RL).")


def convertir_dbm_mw(dbm: Optional[float] = None, mw: Optional[float] = None) -> Dict[str, Any]:
    """Convierte potencia entre dBm y mW: dBm = 10*log10(mW); mW = 10^(dBm/10)."""
    if dbm is not None:
        mw_val = 10 ** (dbm / 10.0)
        return {"dbm": dbm, "mw": mw_val}
    if mw is not None:
        if mw <= 0:
            raise ValueError("La potencia en mW debe ser mayor que cero.")
        dbm_val = 10 * math.log10(mw)
        return {"dbm": dbm_val, "mw": mw}
    raise ValueError("Se requiere un valor en dBm o en mW.")


def convertir_vrms_vpp(vrms: Optional[float] = None, vpp: Optional[float] = None) -> Dict[str, Any]:
    """Convierte entre voltaje RMS y pico a pico para una señal senoidal:
    Vpp = 2*sqrt(2)*Vrms ; Vrms = Vpp / (2*sqrt(2))."""
    factor = 2 * math.sqrt(2)
    if vrms is not None:
        return {"vrms": vrms, "vpp": vrms * factor}
    if vpp is not None:
        return {"vrms": vpp / factor, "vpp": vpp}
    raise ValueError("Se requiere un valor de Vrms o Vpp.")


_COLOR_DIGITS = {
    "negro": 0, "black": 0,
    "marron": 1, "marrón": 1, "cafe": 1, "café": 1, "brown": 1,
    "rojo": 2, "red": 2,
    "naranja": 3, "orange": 3,
    "amarillo": 4, "yellow": 4,
    "verde": 5, "green": 5,
    "azul": 6, "blue": 6,
    "violeta": 7, "morado": 7, "purple": 7, "violet": 7,
    "gris": 8, "grey": 8, "gray": 8,
    "blanco": 9, "white": 9,
}

_COLOR_MULTIPLIER = dict(_COLOR_DIGITS)
_COLOR_MULTIPLIER.update({
    "oro": -1, "dorado": -1, "gold": -1,
    "plata": -2, "plateado": -2, "silver": -2,
})

_COLOR_TOLERANCE = {
    "marron": 1.0, "marrón": 1.0, "cafe": 1.0, "café": 1.0, "brown": 1.0,
    "rojo": 2.0, "red": 2.0,
    "verde": 0.5, "green": 0.5,
    "azul": 0.25, "blue": 0.25,
    "violeta": 0.1, "morado": 0.1, "purple": 0.1, "violet": 0.1,
    "gris": 0.05, "grey": 0.05, "gray": 0.05,
    "oro": 5.0, "dorado": 5.0, "gold": 5.0,
    "plata": 10.0, "plateado": 10.0, "silver": 10.0,
}


def decodificar_color_resistencia(bands: List[str]) -> Dict[str, Any]:
    """Decodifica el valor de una resistencia a partir de sus bandas de color.

    Soporta 4 bandas (2 dígitos + multiplicador + tolerancia) y
    5 bandas (3 dígitos + multiplicador + tolerancia).
    """
    if not bands or len(bands) not in (4, 5):
        raise ValueError("Se requieren 4 o 5 bandas de color.")

    colores = [str(b).strip().lower() for b in bands]
    n_digits = 3 if len(colores) == 5 else 2

    try:
        digitos = [_COLOR_DIGITS[c] for c in colores[:n_digits]]
        mult_color = colores[n_digits]
        exp = _COLOR_MULTIPLIER[mult_color]
        tol_color = colores[n_digits + 1]
        tolerancia = _COLOR_TOLERANCE.get(tol_color, 20.0)
    except KeyError as e:
        raise ValueError(f"Color de banda no reconocido: {e}")

    valor_base = int("".join(str(d) for d in digitos))
    valor = valor_base * (10 ** exp)

    return {"valor": valor, "tolerancia_pct": tolerancia, "bandas": colores}


_SI_PREFIX_EXPONENT = {
    "nano": -9, "n": -9,
    "micro": -6, "u": -6, "µ": -6,
    "mili": -3, "milli": -3, "m": -3,
    "base": 0, "unidad": 0, "": 0,
    "kilo": 3, "k": 3,
    "mega": 6, "M": 6,
}


def convertir_prefijo_si(value: float, from_prefix: str, to_prefix: str) -> Dict[str, Any]:
    """Convierte un valor numérico entre prefijos SI (nano, micro, mili, base, kilo, mega)."""
    if value is None:
        raise ValueError("Se requiere un valor numérico.")

    f_key = (from_prefix or "base").strip().lower()
    t_key = (to_prefix or "base").strip().lower()

    if f_key not in _SI_PREFIX_EXPONENT:
        raise ValueError(f"Prefijo de origen no reconocido: {from_prefix}")
    if t_key not in _SI_PREFIX_EXPONENT:
        raise ValueError(f"Prefijo de destino no reconocido: {to_prefix}")

    valor_base = value * (10 ** _SI_PREFIX_EXPONENT[f_key])
    resultado = valor_base / (10 ** _SI_PREFIX_EXPONENT[t_key])

    return {"resultado": resultado, "valor_base_si": valor_base}
