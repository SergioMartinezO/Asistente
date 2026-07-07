import pytest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.electronics.components import Resistencia, ComponentOverloadError
from core.electronics.commercial import buscar_resistencia_comercial
from core.electronics.calculations import calcular_divisor_tension

def test_buscar_resistencia_comercial_desde_standards_json():
    # 102Ω en E24 aproxima a 100Ω utilizando los datos leídos del JSON
    res = buscar_resistencia_comercial(102.0, usar_e96=False)
    assert res.valor == 100.0

def test_divisor_tension_con_efecto_de_carga():
    # Divisor 10V con R1=1000Ω, R2=1000Ω. 
    # Sin carga: Vout = 5V.
    res_sin_carga = calcular_divisor_tension(10.0, 1000.0, 1000.0)
    assert res_sin_carga["vout_ideal"] == 5.0

    # Con carga RL = 1000Ω. R2 || RL = 500Ω.
    # Vout = 10 * 500 / 1500 = 3.333V.
    res_con_carga = calcular_divisor_tension(10.0, 1000.0, 1000.0, rl=1000.0)
    assert pytest.approx(res_con_carga["vout_ideal"], 0.01) == 3.33
