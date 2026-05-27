# actions/proteus_automation.py
import os
import time
import subprocess
import pyautogui
import ctypes

def proteus_automation(parameters: dict, player=None, speak=None):
    action = parameters.get("action", "simulate").lower().strip()
    dsn_path = parameters.get("dsn_path", "").strip()
    exe_path = parameters.get("exe_path", "").strip()
    duration = float(parameters.get("duration", 12.0))

    def log(msg):
        if player:
            player.write_log(f"PROT: {msg}")

    def say(msg):
        if speak:
            speak(msg)
        log(msg)

    # Rutas por defecto del sistema si no se especifican
    if not exe_path:
        exe_path = r"C:\Program Files (x86)\Labcenter Electronics\Proteus 8 Professional\BIN\PDS.EXE"
    
    if not dsn_path:
        # Intenta buscar un circuito por defecto en el escritorio de Sergio
        desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
        dsn_path = os.path.join(desktop_dir, "Circuito_Mixto.DSN")

    if not os.path.exists(exe_path):
        msg = f"No se encontró el ejecutable de Proteus en la ruta especificada: {exe_path}"
        say(msg)
        return msg

    if not os.path.exists(dsn_path):
        msg = f"No se encontró el archivo de diseño de circuito (.DSN) en: {dsn_path}"
        say(msg)
        return msg

    if action == "simulate":
        say(f"Iniciando simulación de Proteus para {os.path.basename(dsn_path)}, Sergio.")
        
        # 1. DPI Awareness para evitar errores de coordenadas
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
            log("Conciencia de DPI configurada.")
        except Exception as e:
            log(f"Error en DPI: {e}")

        # 2. Configurar PyAutoGUI
        pyautogui.FAILSAFE = True
        pyautogui.PAUSE = 1.2

        try:
            # Lanza Proteus con el archivo del circuito
            proc = subprocess.Popen([exe_path, dsn_path])
            time.sleep(6.0) # Espera crítica de renderizado

            # Maximiza
            pyautogui.hotkey('alt', 'space')
            pyautogui.press('x')
            time.sleep(1.5)

            # Ejecutar Simulación (F12 en Proteus)
            log("Enviando comando de simulación (F12)...")
            pyautogui.press('f12')
            
            # Espera de simulación activa
            log(f"Simulación corriendo durante {duration} segundos...")
            time.sleep(duration)

            # Detener Simulación (ESC en Proteus)
            log("Deteniendo simulación (ESC)...")
            pyautogui.press('escape')
            time.sleep(1.5)

            # Cerrar limpio (Alt+F4)
            log("Cerrando Proteus...")
            pyautogui.hotkey('alt', 'f4')
            
            result = f"Simulación de {os.path.basename(dsn_path)} finalizada correctamente."
            say(result)
            return result

        except Exception as e:
            msg = f"Ocurrió un error al automatizar Proteus: {e}"
            say(msg)
            return msg
    else:
        msg = f"Acción de Proteus no reconocida: {action}"
        say(msg)
        return msg