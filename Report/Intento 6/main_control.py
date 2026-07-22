# main_control.py
import serial
import time

# Código Python de control principal (simulación de lógica de comandos de voz)
# En un sistema real, este módulo se comunicaría con el hardware ESP32
# para enviar los comandos de actuación (ON/OFF).

def send_command(command):
    """Simula el envío de un comando al puerto serie."""
    try:
        # ser = serial.Serial('COM3', 9600) # Reemplazar 'COM3' por el puerto real
        # time.sleep(2)
        print(f"DEBUG: Enviando comando '{command}' al hardware...")
        # ser.write(command.encode('utf-8'))
        # ser.close()
        print(f"INFO: Comando '{command}' enviado exitosamente.")
    except Exception as e:
        print(f"ERROR: No se pudo conectar al hardware o enviar el comando: {e}")

def process_voice_command(command):
    """Procesa el comando de voz simulado y determina la acción."""
    command = command.lower()
    if "encender" in command or "prender" in command:
        send_command("LED_ON")
    elif "apagar" in command:
        send_command("LED_OFF")
    else:
        print("ADVERTENCIA: Comando no reconocido.")

if __name__ == "__main__":
    print("Sistema de Control de Iluminación por Voz iniciado.")
    # Simulación de comandos recibidos
    process_voice_command("Encender la luz")
    time.sleep(1)
    process_voice_command("Apagar bombilla")
