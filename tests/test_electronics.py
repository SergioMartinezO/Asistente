import pytest
import sys
import os

# Configuración del path de búsqueda
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.components import Resistencia, Capacitor, Inductor
from core.commercial import buscar_resistencia_comercial

def test_dataclass_resistencia_validaciones():
    r = Resistencia(valor=100.0, potencia_nominal=0.25)
    # 5V aplicados disipan 0.25W -> exacto al límite térmico, debe validar True con factor 1.0
    assert r.validar_seguridad(voltaje_operacion=5.0, factor_seguridad=1.0) is True
    # Con factor 1.5x requerimos 0.375W de límite nominal, por lo que debe invalidar (False)
    assert r.validar_seguridad(voltaje_operacion=5.0, factor_seguridad=1.5) is False

def test_dataclass_capacitor_energia():
    c = Capacitor(valor=10e-6, voltaje_nominal=16.0)
    # Energía a 10V
    e = c.calcular_energia_almacenada(voltaje_aplicado=10.0)
    assert e == 0.5 * 10e-6 * 100.0
    
    with pytest.raises(ValueError):
        # Superar el voltaje nominal de ruptura dieléctrica
        c.calcular_energia_almacenada(voltaje_aplicado=20.0)

def test_dataclass_inductor_saturacion():
    l = Inductor(valor=100e-3, corriente_saturacion=2.0)
    assert l.calcular_energia_almacenada(corriente_aplicada=1.0) == 0.05
    
    with pytest.raises(ValueError):
        l.calcular_energia_almacenada(corriente_aplicada=3.0)

def test_buscar_resistencia_comercial():
    # 102Ω en E24 aproxima a 100Ω
    r24 = buscar_resistencia_comercial(102.0, usar_e96=False)
    assert r24.valor == 100.0
    
    # 102Ω en E96 aproxima a 102Ω exacto
    r96 = buscar_resistencia_comercial(102.0, usar_e96=True)
    assert r96.valor == 102.0
