import pytest
import sys
import os

# Configurar ruta absoluta para el path de python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actions.electronics import ElectronicsAction

@pytest.fixture
def action():
    return ElectronicsAction()

def test_buscar_comercial_e24(action):
    # El valor teórico 102Ω en E24 (tolerancia 5%) aproxima a 100Ω
    res = action.buscar_comercial(102.0, usar_e96=False)
    assert res.valor_comercial == 100.0
    assert res.serie == "E24"

def test_buscar_comercial_e96(action):
    # El valor teórico 102Ω en E96 (tolerancia 1%) es un valor normalizado base y debe retornar exactamente 102Ω
    res = action.buscar_comercial(102.0, usar_e96=True)
    assert res.valor_comercial == 102.0
    assert res.serie == "E96"
    assert res.error_relativo == 0.0

def test_limites_termicos_y_encapsulados(action):
    # Para una disipación de 0.1W, con factor de seguridad de 1.5x requerimos 0.15W seguros.
    # El encapsulado inmediato superior de 1/8W (0.125W) no es suficiente, por lo que debe sugerir 1/4W (0.25W)
    res = action.buscar_comercial(100.0, potencia_calc=0.10)
    assert res.potencia_nominal_sugerida == 0.25
    assert "1/4W" in res.encapsulado_sugerido

def test_limite_sobrecarga_critico(action):
    # Si la disipación es muy alta (ej. 10W), debe sugerir un encapsulado especial
    res = action.buscar_comercial(10.0, potencia_calc=10.0)
    assert "Disipador" in res.encapsulado_sugerido
