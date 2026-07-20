# =======================================================================
# PROYECTO  : Dispositivo de control de bombillo por comandos de voz
# AUTOR     : Sergio Antonio Martinez Orozco
# INSTITUCIÓN: UNAD
# FECHA     : 18/07/2026
# VERSIÓN   : v1.0
# DESCRIPCIÓN: Control de dispositivo electrónico con ESP32.
#              Adquisición de señal → procesamiento → actuación
#              → respaldo en nube (si aplica).
# =======================================================================

import time
import sys

# ── Constantes de configuración ─────────────────────────────────────────
PIN_SENSOR    = 34          # GPIO34 – entrada analógica ADC1
PIN_ACTUADOR  = 23          # GPIO23 – salida PWM / digital
UMBRAL_ALTO   = 70.0        # % del rango ADC – umbral de activación
UMBRAL_BAJO   = 30.0        # % del rango ADC – histéresis de desactivación
PERIODO_MS    = 500         # ms – período de muestreo (2 Hz)
VOLT_REF      = 3.3         # V – tensión de referencia ADC
RESOLUCION    = 4095        # 12-bit ADC (2^12 - 1)

# ── Variables de estado ──────────────────────────────────────────────────
estado_actuador = False     # False = APAGADO, True = ENCENDIDO
log_sesion: list = []       # registro de eventos de la sesión


# ── Funciones de soporte ─────────────────────────────────────────────────

def leer_sensor(pin: int) -> float:
    """
    Lee el valor del ADC en el pin indicado y lo convierte a porcentaje
    del rango completo (0–100 %).
    Retorna: float en rango [0.0, 100.0]
    """
    # En MicroPython / hardware real usar: machine.ADC(pin).read()
    # Aquí se simula para entorno de prueba.
    import random
    lectura_raw = random.randint(0, RESOLUCION)   # ← reemplazar por lectura real
    return (lectura_raw / RESOLUCION) * 100.0


def controlar_actuador(activar: bool, pin: int) -> None:
    """
    Activa o desactiva el actuador conectado al pin de salida.
    Implementa lógica anti-rebote de hardware (histéresis).
    """
    global estado_actuador
    if activar == estado_actuador:
        return  # sin cambio de estado: no hacer nada
    estado_actuador = activar
    accion = "ENCENDIDO" if activar else "APAGADO"
    # En hardware real: machine.Pin(pin, machine.Pin.OUT).value(int(activar))
    print(f"[ACTUADOR] GPIO{pin} → {accion}")


def registrar_evento(nivel: str, mensaje: str) -> None:
    """
    Registra un evento en el log de sesión con marca de tiempo.
    nivel: 'INFO' | 'WARN' | 'ERROR'
    """
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    entrada = f"[{ts}] [{nivel}] {mensaje}"
    log_sesion.append(entrada)
    print(entrada)


# ── Bucle principal de control ───────────────────────────────────────────

def setup() -> None:
    """Inicialización del sistema antes del bucle de control."""
    registrar_evento("INFO", f"Sistema iniciado — {project_title}")
    registrar_evento("INFO", f"Umbrales: ALTO={UMBRAL_ALTO}% BAJO={UMBRAL_BAJO}%")
    registrar_evento("INFO", "Hardware inicializado correctamente.")


def loop() -> None:
    """
    Bucle principal de adquisición → decisión → actuación.
    Se ejecuta de forma indefinida con período PERIODO_MS.
    """
    while True:
        try:
            valor = leer_sensor(PIN_SENSOR)
            voltaje = (valor / 100.0) * VOLT_REF

            # ── Lógica de control con histéresis ─────────────────
            if valor >= UMBRAL_ALTO and not estado_actuador:
                controlar_actuador(True, PIN_ACTUADOR)
                registrar_evento("INFO", f"Activación: {valor:.1f}% ({voltaje:.2f} V)")

            elif valor <= UMBRAL_BAJO and estado_actuador:
                controlar_actuador(False, PIN_ACTUADOR)
                registrar_evento("INFO", f"Desactivación: {valor:.1f}% ({voltaje:.2f} V)")

            time.sleep(PERIODO_MS / 1000.0)

        except KeyboardInterrupt:
            registrar_evento("INFO", "Bucle detenido por el usuario.")
            controlar_actuador(False, PIN_ACTUADOR)  # seguridad: apagar actuador
            break

        except Exception as exc:
            registrar_evento("ERROR", f"Excepción en loop: {exc}")
            time.sleep(2.0)  # pausa antes de reintentar


# ── Punto de entrada ─────────────────────────────────────────────────────

if __name__ == "__main__":
    setup()
    loop()
    sys.exit(0)
