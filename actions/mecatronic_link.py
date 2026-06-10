import importlib
import asyncio
from typing import Dict, Any, Optional, Callable
from actions.base import BaseAction

class MecatronicLinkAction(BaseAction):
    """Acción que permite establecer enlaces bidireccionales con hardware usando pyserial."""

    @property
    def name(self) -> str:
        return "mecatronic_link"

    @property
    def description(self) -> str:
        return (
            "Permite leer y escribir datos a microcontroladores (Arduino/ESP32) por puerto serie. "
            "Parámetros: port (COM/tty), baudrate, command (opcional para escribir)."
        )

    async def execute(
        self,
        parameters: Dict[str, Any],
        player: Optional[Any] = None,
        speak_callback: Optional[Callable[[str], None]] = None
    ) -> str:
        port = parameters.get("port", "COM3")
        baudrate = int(parameters.get("baudrate", 9600))
        command = parameters.get("command")

        def say(msg: str) -> None:
            if player and hasattr(player, "write_log"):
                player.write_log(f"HARDWARE: {msg}")
            if speak_callback:
                speak_callback(msg)

        try:
            serial = importlib.import_module("serial")
            say(f"Abriendo conexión serie en {port} a {baudrate} baudios...")
            
            # Ejecución en ejecutor para evitar bloquear el event loop con E/S síncrona de pyserial
            loop = asyncio.get_event_loop()
            
            def _interact():
                with serial.Serial(port, baudrate, timeout=2.0) as ser:
                    if command:
                        ser.write(f"{command}\n".encode('utf-8'))
                        return f"Comando '{command}' enviado. Puerto cerrado."
                    else:
                        # Leer unas líneas de telemetría de muestra
                        lines = []
                        for _ in range(5):
                            line = ser.readline().decode('utf-8', errors='ignore').strip()
                            if line:
                                lines.append(line)
                        return "Lecturas de telemetría:\n" + "\n".join(lines)

            result = await loop.run_in_executor(None, _interact)
            say("Interacción de hardware completada.")
            return result

        except ImportError:
            err = "Biblioteca 'pyserial' no está instalada. Ejecute 'pip install pyserial' en el entorno virtual."
            say(err)
            return err
        except Exception as e:
            err = f"Error al acceder al hardware en {port}: {str(e)}"
            say(err)
            return err
