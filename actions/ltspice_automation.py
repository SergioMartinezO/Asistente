# actions/ltspice_automation.py
import os
import re
import subprocess
import sys

def ltspice_automation(parameters: dict, player=None, speak=None):
    action = parameters.get("action", "simulate").lower().strip()
    asc_path = parameters.get("asc_path", "").strip()
    exe_path = parameters.get("exe_path", "").strip()

    def log(msg):
        if player:
            player.write_log(f"LTSP: {msg}")

    def say(msg):
        if speak:
            speak(msg)
        log(msg)

    # 1. Búsqueda de ejecutables comunes de LTspice en Windows
    rutas_comunes = [
        r"C:\Program Files\ADI\LTspice\LTspice.exe",
        r"C:\Program Files\LTC\LTspiceXVII\XVIIist.exe",
        r"C:\Program Files\LTC\LTspiceXVII\LTspiceXVII.exe",
        r"C:\Program Files\LTC\LTspiceIV\scad3.exe",
    ]

    if not exe_path:
        for r in rutas_comunes:
            if os.path.exists(r):
                exe_path = r
                break
        else:
            exe_path = "LTspice.exe" # Buscar en el PATH

    if not asc_path:
        # Busca un archivo por defecto en el Escritorio
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        asc_path = os.path.join(desktop_dir, "Filtro_Paso_Bajo.asc")

    # Si es otra plataforma, intentar buscar en PATH
    if sys.platform != "win32":
        exe_path = "ltspice"

    if action == "simulate":
        if not os.path.exists(asc_path):
            msg = f"No se encontró el archivo de simulación (.asc) en la ruta: {asc_path}"
            say(msg)
            return msg

        say(f"Lanzando simulación en lote de LTspice para {os.path.basename(asc_path)}...")
        
        try:
            # Comando de ejecución en lote (-b es Batch, -Run inicia la simulación inmediatamente)
            # En lote, LTspice no abre ventana y termina cuando acaba la simulación.
            cmd = [exe_path, "-b", "-Run", asc_path]
            log(f"Comando: {' '.join(cmd)}")
            
            result_proc = subprocess.run(cmd, capture_output=True, text=True, timeout=40)
            
            # El archivo log generado tiene el mismo nombre que el .asc pero con extensión .log
            log_path = os.path.splitext(asc_path)[0] + ".log"
            
            if not os.path.exists(log_path):
                # Intentar en minúsculas
                log_path = os.path.splitext(asc_path)[0] + ".LOG"

            if os.path.exists(log_path):
                try:
                    # Leer archivo .log (a veces codificado en UTF-16 LE)
                    try:
                        with open(log_path, "r", encoding="utf-16-le", errors="ignore") as f:
                            log_content = f.read()
                    except Exception:
                        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                            log_content = f.read()

                    # Extraer sección de mediciones (.meas o .measure)
                    mediciones = []
                    lineas = log_content.splitlines()
                    
                    # LTspice escribe los resultados de .meas en el log
                    capturar = False
                    for line in lineas:
                        if "--- Measurements ---" in line:
                            capturar = True
                            continue
                        if capturar:
                            # Si empieza otra sección importante, paramos
                            if line.startswith("---") or line.strip() == "":
                                if mediciones: # Si ya capturamos algo, detenemos
                                    break
                            mediciones.append(line.strip())

                    # Si no se encontró la sección --- Measurements ---, buscar patrones
                    if not mediciones:
                        for line in lineas:
                            # Patrón típico de mediciones: "name: value at..." o "name=value"
                            if ":" in line or "=" in line:
                                if any(x in line.lower() for x in ["step", "failed", "error"]):
                                    continue
                                mediciones.append(line.strip())

                    mediciones_str = "\n".join(mediciones[:15]) if mediciones else "No se detectaron comandos .meas configurados en el circuito."

                    msg = (
                        f"Simulación de LTspice completada con éxito.\n"
                        f"Resultados de mediciones extraídos de {os.path.basename(log_path)}:\n"
                        f"{mediciones_str}"
                    )
                    say(msg)
                    return msg

                except Exception as e_file:
                    msg = f"Simulación finalizada, pero no se pudo leer el archivo log: {e_file}"
                    say(msg)
                    return msg
            else:
                msg = "Simulación completada. No se generó archivo .log de telemetría."
                say(msg)
                return msg

        except subprocess.TimeoutExpired:
            msg = "La simulación de LTspice tardó demasiado tiempo y fue cancelada."
            say(msg)
            return msg
        except Exception as e:
            msg = f"Fallo al invocar LTspice: {e}. Verifique que la ruta sea correcta."
            say(msg)
            return msg
    else:
        msg = f"Acción de LTspice no reconocida: {action}"
        say(msg)
        return msg
