import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.electronics.components import Resistencia, Capacitor, ComponentOverloadError
from core.electronics.commercial import buscar_resistencia_comercial
from core.electronics.calculations import calcular_ohm

def test_excepcion_sobrecarga_resistencia():
    r = Resistencia(valor=100.0, potencia_nominal=0.25)
    # 5V en 100Ω disipa exactamente 0.25W. Con un factor de seguridad de 1.5x, requerimos 0.375W nominales.
    # Debe lanzar ComponentOverloadError debido a la sobrecarga térmica simulada.
    with pytest.raises(ComponentOverloadError):
        r.validar_seguridad(voltaje_operacion=5.0, factor_seguridad=1.5)

def test_calculo_ohm_con_sobrecarga():
    # 10V en un resistor comercial aproximado de 100Ω (disipa 1W, superando los 0.25W nominales de E24)
    # Debe disparar la alarma de sobrecarga de forma automática.
    with pytest.raises(ComponentOverloadError):
        calcular_ohm(v=10.0, i=0.1)

def test_buscar_resistencia_comercial_e24():
    res = buscar_resistencia_comercial(102.0, usar_e96=False)
    assert res.valor == 100.0
