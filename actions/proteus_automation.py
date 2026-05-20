# ====================================================================
# SCRIPT: proteus_automation.py
# DESCRIPCIÓN: Control determinista de carga y simulación en Proteus VSM
# ====================================================================

import os
import time
import subprocess
import pyautogui
import ctypes

def inicializar_entorno():
    """Configura las variables de seguridad y entorno de interfaz en Windows 11."""
    # 1. Forzar conciencia de DPI (DPI Awareness) para mitigar errores de coordenadas por escalado
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(2) # PROCESS_PER_MONITOR_DPI_AWARE
        print("[INFO] Conciencia de DPI configurada exitosamente.")
    except Exception as e:
        print(f"[ADVERTENCIA] No se pudo establecer la conciencia de DPI: {e}")

    # 2. Protocolo de seguridad FailSafe
    pyautogui.FAILSAFE = True  # Mover el cursor a la esquina superior izquierda detiene el script de inmediato
    pyautogui.PAUSE = 1.2      # Retardo estándar (segundos) entre instrucciones GUI

def ejecutar_simulacion_proteus(ruta_exe, ruta_proyecto):
    """Lanza la instancia de Proteus, maximiza, simula mediante atajos nativos y cierra."""
    if not os.path.exists(ruta_exe):
        print(f"[ERROR] Ejecutable de Proteus no hallado en la ruta: {ruta_exe}")
        return

    print("[INFO] Iniciando instancia de Proteus VSM con archivo de diseño...")
    # Lanza Proteus inyectando el archivo de circuito como argumento de línea de comandos
    subprocess.Popen([ruta_exe, ruta_proyecto])
    
    # Tiempo de espera crítico para la inicialización del entorno gráfico
    time.sleep(6.0)

    print("[INFO] Maximizando ventana principal de Proteus...")
    # Atajo nativo del sistema operativo para maximizar la ventana activa
    pyautogui.hotkey('alt', 'space')
    pyautogui.press('x')
    time.sleep(1.5)

    print("[INFO] Enviando pulso de ejecución al motor de simulación (F12)...")
    # F12 es el shortcut nativo de Proteus para iniciar el procesamiento analógico/digital
    pyautogui.press('f12')
    
    # Ventana de tiempo establecida para evaluar la ejecución del circuito
    print("[INFO] Simulación activa. Ejecutando telemetría por 12 segundos...")
    time.sleep(12.0)

    print("[INFO] Enviando pulso de detención de simulación (ESC)...")
    pyautogui.press('escape')
    time.sleep(1.5)

    print("[INFO] Cerrando la aplicación de manera limpia (Alt+F4)...")
    pyautogui.hotkey('alt', 'f4')

if __name__ == "__main__":
    inicializar_entorno()
    
    # AJUSTE DE RUTAS: Defina las rutas reales según su entorno local
    RUTA_PROTEUS_EXE = r"C:\Program Files (x86)\Labcenter Electronics\Proteus 8 Professional\BIN\PDS.EXE"
    RUTA_PROYECTO_DSN = r"C:\Users\Sergio\Desktop\Circuito_Mixto.DSN"
    
    ejecutar_simulacion_proteus(RUTA_PROTEUS_EXE, RUTA_PROYECTO_DSN)