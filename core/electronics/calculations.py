from core.electronics.components import Resistencia, ComponentOverloadError
from core.electronics.commercial import buscar_resistencia_comercial
from typing import Dict, Any

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

def calcular_divisor_tension(vin: float, r1: float, r2: float) -> Dict[str, Any]:
    """Calcula un divisor de tensión y verifica la seguridad de R1 y R2."""
    if (r1 + r2) == 0:
        raise ValueError("Divisor por cero en R1 + R2.")
    
    i_lazo = vin / (r1 + r2)
    p_r1 = (i_lazo ** 2) * r1
    p_r2 = (i_lazo ** 2) * r2

    r1_com = buscar_resistencia_comercial(r1)
    r2_com = buscar_resistencia_comercial(r2)

    # Validar disipación en el lazo
    r1_com.validar_seguridad(i_lazo * r1_com.valor)
    r2_com.validar_seguridad(i_lazo * r2_com.valor)

    vout_com = vin * r2_com.valor / (r1_com.valor + r2_com.valor)

    return {
        "vout_ideal": vin * r2 / (r1 + r2),
        "vout_comercial": vout_com,
        "p_r1": p_r1,
        "p_r2": p_r2,
        "r1_com": r1_com,
        "r2_com": r2_com
    }
