import importlib
from typing import Dict, Any, Optional, Callable
from actions.base import BaseAction

# ──────────────────────────────────────────────────────────────────────
# Fundamento Teórico: Respuesta en Frecuencia (Diagrama de Bode)
#
# La función de transferencia de un sistema lineal e invariante en el tiempo
# (LTI) se define en el dominio de Laplace como:
#
#   H(s) = Y(s) / X(s) = (b_m s^m + ... + b_1 s + b_0) / (a_n s^n + ... + a_1 s + a_0)
#
# Para obtener la respuesta en frecuencia, evaluamos en s = jω, donde ω
# es la frecuencia angular (rad/s).
#   El diagrama de Bode grafica:
#     1. Magnitud en decibelios (dB): A(ω) = 20 * log10(|H(jω)|)
#     2. Fase en grados: φ(ω) = arg(H(jω)) * (180 / π)
# ──────────────────────────────────────────────────────────────────────

class MatlabLinkAction(BaseAction):
    """Acción que provee interfaz de simulación y graficado LTI mediante MATLAB Engine."""

    @property
    def name(self) -> str:
        return "matlab_link"

    @property
    def description(self) -> str:
        return (
            "Automatiza simulaciones de sistemas y diagramas de Bode interactuando con MATLAB. "
            "Parámetros: num (numerador), den (denominador)."
        )

    async def execute(
        self,
        parameters: Dict[str, Any],
        player: Optional[Any] = None,
        speak_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        num = parameters.get("num", [1.0])
        den = parameters.get("den", [1.0, 1.0])

        def say(msg: str) -> None:
            if player and hasattr(player, "write_log"):
                player.write_log(f"MATLAB: {msg}")
            if speak_callback:
                speak_callback(msg)

        say("Iniciando motor de simulación de MATLAB...")

        try:
            # Importación dinámica del motor de Matlab para evitar excepciones si no está instalado
            matlab_engine = importlib.import_module("matlab.engine")
            eng = matlab_engine.start_matlab()
            
            # Convertir coeficientes a tipos nativos de MATLAB
            m_num = matlab_engine.double(num)
            m_den = matlab_engine.double(den)

            say("Generando la función de transferencia en el espacio de Laplace...")
            eng.eval("pkg load control", nargout=0)  # Cargar toolbox de control si se usa alternativa libre o config compatible
            eng.workspace['num'] = m_num
            eng.workspace['den'] = m_den
            eng.eval("sys = tf(num, den);", nargout=0)
            
            say("Graficando el Diagrama de Bode...")
            eng.eval("figure; bode(sys); grid on;", nargout=0)
            
            result = f"Diagrama de Bode generado exitosamente para H(s) = {num} / {den}."
            say(result)
            return result

        except ImportError:
            # Fallback elegante usando scipy/matplotlib en caso de ausencia de la licencia de MATLAB
            try:
                say("MATLAB Engine no detectado en el entorno local. Utilizando motor alternativo (SciPy)...")
                import numpy as np
                from scipy import signal
                import matplotlib.pyplot as plt

                sys = signal.TransferFunction(num, den)
                w, mag, phase = signal.bode(sys)

                plt.figure(figsize=(10, 6))
                plt.subplot(2, 1, 1)
                plt.semilogx(w, mag)
                plt.title("Diagrama de Bode (Motor de Respaldo SciPy)")
                plt.ylabel("Magnitud (dB)")
                plt.grid(True, which="both")

                plt.subplot(2, 1, 2)
                plt.semilogx(w, phase)
                plt.ylabel("Fase (grados)")
                plt.xlabel("Frecuencia (rad/s)")
                plt.grid(True, which="both")
                
                plt.tight_layout()
                plt.show(block=False)

                result = "Simulación alternativa completada. Gráfico mostrado mediante Matplotlib."
                say(result)
                return result

            except Exception as e:
                err_msg = f"Fallo en el motor alternativo de simulación: {str(e)}"
                say(err_msg)
                return err_msg

        except Exception as e:
            err_msg = f"Error durante la automatización de MATLAB: {str(e)}"
            say(err_msg)
            return err_msg
