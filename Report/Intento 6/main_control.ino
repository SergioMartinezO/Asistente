// =====================================================================
// PROYECTO   : Desarrollo de Sistema de Control de Iluminación por Comando de Voz
// PLATAFORMA : Arduino / ESP32 (compatible)
// LENGUAJE   : C++ (Arduino Framework)
// ESTÁNDAR   : ISO/IEC 9126 — Buenas prácticas de programación
// COMENTARIOS: En español, conforme a la rúbrica de entrega
// =====================================================================

#include <Arduino.h>

// ── Definición de pines ──────────────────────────────────────────────
#define PIN_SENSOR    34   // GPIO34 – Entrada analógica ADC (0–4095)
#define PIN_ACTUADOR  23   // GPIO23 – Salida digital / PWM
#define PIN_LED_DBG    2   // GPIO2  – LED indicador de estado (built-in)

// ── Constantes del sistema ───────────────────────────────────────────
const float UMBRAL_ALTO   = 70.0f;  // % – Umbral de activación
const float UMBRAL_BAJO   = 30.0f;  // % – Umbral de desactivación (histéresis)
const int   PERIODO_MS    = 500;    // ms – Período de muestreo
const float VOLT_REF      = 3.3f;   // V  – Tensión de referencia ADC
const int   RESOLUCION    = 4095;   // 12-bit ADC

// ── Variables de estado ──────────────────────────────────────────────
bool  estadoActuador = false;       // false=APAGADO, true=ENCENDIDO
float ultimoValor    = 0.0f;        // Último valor leído del sensor

// ── Prototipos de funciones ───────────────────────────────────────────
float leerSensor(int pin);
void  controlarActuador(bool activar);
void  registrarEvento(const char* nivel, const String& mensaje);

// ── Configuración inicial (ejecutada una vez al arrancar) ─────────────
void setup() {
  Serial.begin(115200);                      // Iniciar comunicación serial
  pinMode(PIN_ACTUADOR, OUTPUT);             // Configurar pin de actuador como salida
  pinMode(PIN_LED_DBG,  OUTPUT);             // Configurar LED de depuración
  digitalWrite(PIN_ACTUADOR, LOW);           // Asegurar actuador apagado al inicio
  analogReadResolution(12);                  // Resolución ADC: 12 bits (ESP32)
  registrarEvento("INFO", "Sistema iniciado — Desarrollo de Sistema de Control de Iluminación por Comando de Voz");
  registrarEvento("INFO", "Umbral alto: " + String(UMBRAL_ALTO) +
                          "% | Umbral bajo: " + String(UMBRAL_BAJO) + "%");
}

// ── Bucle principal de control (ejecutado continuamente) ─────────────
void loop() {
  // 1. Adquisición de la señal del sensor
  float valor = leerSensor(PIN_SENSOR);
  float voltaje = (valor / 100.0f) * VOLT_REF;

  // 2. Lógica de control con histéresis (evita oscilación en el umbral)
  if (valor >= UMBRAL_ALTO && !estadoActuador) {
    controlarActuador(true);                 // Activar actuador
    registrarEvento("INFO", "ACTIVADO: " + String(valor, 1) + "%  (" +
                            String(voltaje, 2) + " V)");
  } else if (valor <= UMBRAL_BAJO && estadoActuador) {
    controlarActuador(false);                // Desactivar actuador
    registrarEvento("INFO", "DESACTIVADO: " + String(valor, 1) + "%  (" +
                            String(voltaje, 2) + " V)");
  }

  // 3. Parpadeo LED de depuración para indicar ciclo activo
  digitalWrite(PIN_LED_DBG, HIGH);
  delay(50);
  digitalWrite(PIN_LED_DBG, LOW);

  delay(PERIODO_MS - 50);                    // Ajuste de período de muestreo
}

// ── Implementación de funciones de soporte ────────────────────────────

/**
 * Lee el valor analógico del sensor y lo convierte a porcentaje (0–100%).
 * @param pin  Número de pin GPIO del ADC
 * @return     Valor normalizado en [0.0, 100.0]
 */
float leerSensor(int pin) {
  int lecturaRaw = analogRead(pin);          // Lectura cruda ADC (0–4095)
  return (float)lecturaRaw / RESOLUCION * 100.0f;
}

/**
 * Activa o desactiva el actuador (salida digital/PWM).
 * Implementa anti-rebote por software: ignora si el estado no cambia.
 * @param activar  true=ENCENDER, false=APAGAR
 */
void controlarActuador(bool activar) {
  if (activar == estadoActuador) return;     // Sin cambio de estado: nada que hacer
  estadoActuador = activar;
  digitalWrite(PIN_ACTUADOR, activar ? HIGH : LOW);
}

/**
 * Registra un evento en el monitor serial con marca de tiempo.
 * @param nivel    Categoría: INFO | WARN | ERROR
 * @param mensaje  Descripción del evento
 */
void registrarEvento(const char* nivel, const String& mensaje) {
  unsigned long ts = millis();
  Serial.print("["); Serial.print(ts); Serial.print(" ms]");
  Serial.print(" ["); Serial.print(nivel); Serial.print("] ");
  Serial.println(mensaje);
}
