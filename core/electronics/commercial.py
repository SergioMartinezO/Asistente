import math
import bisect
import json
import os
from typing import List
from core.electronics.components import Resistencia

# Configuración del path absoluto para estándares
CONFIG_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'standards.json'))

# Caché en memoria para evitar accesos repetitivos a disco
_SERIES_CACHE = {}

def _cargar_serie(nombre: str) -> List[float]:
    """Carga de manera perezosa (lazy load) y segura los valores estáticos de las series desde JSON."""
    global _SERIES_CACHE
    if nombre not in _SERIES_CACHE:
        try:
            with open(CONFIG_PATH, 'r') as file:
                data = json.load(file)
                _SERIES_CACHE[nombre] = data[nombre]
        except Exception as e:
            # Fallback en caso de fallo de lectura de archivo de configuración
            if nombre == "E24":
                _SERIES_CACHE["E24"] = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2, 6.8, 7.5, 8.2, 9.1]
            else:
                raise RuntimeError(f"Fallo al cargar base de datos de estándares electrónicos: {str(e)}")
    return _SERIES_CACHE[nombre]

def buscar_resistencia_comercial(
    valor_ideal: float, 
    usar_e96: bool = False, 
    potencia_nominal: float = 0.25
) -> Resistencia:
    """Encuentra la resistencia comercial más cercana en la serie E24 o E96 (O(log N))."""
    if valor_ideal <= 0:
        raise ValueError("El valor ideal de resistencia debe ser estrictamente positivo.")

    exponente = math.floor(math.log10(valor_ideal))
    mantisa = valor_ideal / (10 ** exponente)

    serie_nombre = "E96" if usar_e96 else "E24"
    base = _cargar_serie(serie_nombre)
    tolerancia = 1.0 if usar_e96 else 5.0

    idx = bisect.bisect_left(base, mantisa)

    if idx == 0:
        cercano = base[0]
    elif idx == len(base):
        cercano = base[-1]
    else:
        izq = base[idx - 1]
        der = base[idx]
        cercano = izq if abs(izq - mantisa) < abs(der - mantisa) else der

    valor_comercial = cercano * (10 ** exponente)
    
    return Resistencia(
        valor=valor_comercial,
        potencia_nominal=potencia_nominal,
        tolerancia=tolerancia
    )
