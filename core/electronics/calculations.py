from core.electronics.components import Resistencia, ComponentOverloadError
from core.electronics.commercial import buscar_resistencia_comercial
from typing import Dict, Any, Optional

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
