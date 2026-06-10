import unittest
import sys
import os

# Asegurar importación correcta agregando la raíz al path de python
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from actions.electronics import ElectronicsAction

class TestElectronicsAction(unittest.TestCase):
    def setUp(self):
        self.action = ElectronicsAction()

    def test_buscar_comercial_e24(self):
        # El valor teórico 102Ω en E24 (tolerancia 5%) debería aproximar a 100Ω
        res = self.action.buscar_comercial(102.0, usar_e96=False)
        self.assertEqual(res.valor_comercial, 100.0)
        self.assertEqual(res.serie, "E24")

    def test_buscar_comercial_e96(self):
        # El valor teórico 102Ω en E96 (tolerancia 1%) debería aproximar a 102Ω ya que es base normalizada
        res = self.action.buscar_comercial(102.0, usar_e96=True)
        self.assertEqual(res.valor_comercial, 102.0)
        self.assertEqual(res.serie, "E96")
        self.assertEqual(res.error_relativo, 0.0)

    def test_error_relativo_resistencia(self):
        # Calcular error relativo para un valor no estándar: 1050Ω
        # E24 más cercano: 1000Ω o 1100Ω. 1000Ω tiene 5% de error. 1100 tiene ~4.76%.
        # E24 tiene 1.0 y 1.1 -> 1000 y 1100.
        res = self.action.buscar_comercial(1050.0, usar_e96=False)
        self.assertIn(res.valor_comercial, [1000.0, 1100.0])
        self.assertLess(res.error_relativo, 5.0)

if __name__ == '__main__':
    unittest.main()
