import math

def mechatronics(parameters: dict, player=None, speak=None):
    action = parameters.get("action", "").lower()

    def log(msg):
        if player:
            player.write_log(f"MECA: {msg}")

    def say(msg):
        if speak:
            speak(msg)
        log(msg)

    # ── Torque y potencia mecánica ───────────────────────────────
    if action == "torque":
        fuerza   = parameters.get("force")
        distancia= parameters.get("distance")
        torque   = parameters.get("torque")
        if fuerza and distancia:
            t = float(fuerza) * float(distancia)
            result = f"Torque = {t:.4f} N·m (F={fuerza}N, d={distancia}m)"
        elif torque and distancia:
            f = float(torque) / float(distancia)
            result = f"Fuerza = {f:.4f} N (T={torque}N·m, d={distancia}m)"
        elif torque and fuerza:
            d = float(torque) / float(fuerza)
            result = f"Distancia = {d:.4f} m (T={torque}N·m, F={fuerza}N)"
        else:
            say("Necesito al menos dos valores: fuerza, distancia o torque.")
            return "Faltan parámetros."
        say(result)
        return result

    # ── Potencia mecánica ────────────────────────────────────────
    elif action == "potencia":
        torque = parameters.get("torque")
        rpm    = parameters.get("rpm")
        fuerza = parameters.get("force")
        vel    = parameters.get("velocity")
        if torque and rpm:
            w = float(rpm) * 2 * math.pi / 60
            p = float(torque) * w
            result = f"Potencia = {p:.4f} W = {p/746:.4f} HP (T={torque}N·m, {rpm}RPM)"
        elif fuerza and vel:
            p = float(fuerza) * float(vel)
            result = f"Potencia = {p:.4f} W = {p/746:.4f} HP (F={fuerza}N, v={vel}m/s)"
        else:
            say("Necesito torque+RPM o fuerza+velocidad.")
            return "Faltan parámetros."
        say(result)
        return result

    # ── Conversión RPM ↔ rad/s ───────────────────────────────────
    elif action == "rpm_rad":
        rpm  = parameters.get("rpm")
        rads = parameters.get("rad_s")
        if rpm is not None:
            w = float(rpm) * 2 * math.pi / 60
            result = f"{rpm} RPM = {w:.4f} rad/s"
        elif rads is not None:
            r = float(rads) * 60 / (2 * math.pi)
            result = f"{rads} rad/s = {r:.4f} RPM"
        else:
            say("Necesito RPM o rad/s.")
            return "Faltan parámetros."
        say(result)
        return result

    # ── Relación de transmisión ──────────────────────────────────
    elif action == "transmision":
        dientes_entrada = parameters.get("teeth_input")
        dientes_salida  = parameters.get("teeth_output")
        rpm_entrada     = parameters.get("rpm_input")
        if dientes_entrada and dientes_salida:
            ratio = float(dientes_salida) / float(dientes_entrada)
            result = f"Relación de transmisión = {ratio:.4f}"
            if rpm_entrada:
                rpm_sal = float(rpm_entrada) / ratio
                result += f" | RPM salida = {rpm_sal:.2f} RPM"
        else:
            say("Necesito dientes de entrada y salida.")
            return "Faltan parámetros."
        say(result)
        return result

    # ── Cinemática lineal ────────────────────────────────────────
    elif action == "cinematica":
        v0 = float(parameters.get("v0", 0))
        vf = parameters.get("vf")
        a  = parameters.get("acceleration")
        t  = parameters.get("time")
        d  = parameters.get("distance")
        results = []
        if vf is not None and a is not None and t is None:
            pass
        if v0 is not None and a is not None and t is not None:
            vf_calc = v0 + float(a) * float(t)
            d_calc  = v0 * float(t) + 0.5 * float(a) * float(t)**2
            results.append(f"Vf = {vf_calc:.4f} m/s")
            results.append(f"d = {d_calc:.4f} m")
        elif v0 is not None and vf is not None and a is not None:
            t_calc = (float(vf) - v0) / float(a)
            d_calc = (float(vf)**2 - v0**2) / (2 * float(a))
            results.append(f"t = {t_calc:.4f} s")
            results.append(f"d = {d_calc:.4f} m")
        elif v0 is not None and vf is not None and t is not None:
            a_calc = (float(vf) - v0) / float(t)
            d_calc = (v0 + float(vf)) / 2 * float(t)
            results.append(f"a = {a_calc:.4f} m/s²")
            results.append(f"d = {d_calc:.4f} m")
        else:
            say("Necesito al menos 3 de los 4 valores: v0, vf, aceleración, tiempo.")
            return "Faltan parámetros."
        result = " | ".join(results)
        say(result)
        return result

    # ── Selección de motores ─────────────────────────────────────
    elif action == "motor_info":
        motores = {
            "dc": (
                "Motor DC: control de velocidad simple con PWM. "
                "Ideal para robots, ventiladores, bombas. "
                "Control: puente H (L298N, L293D). "
                "Velocidad proporcional al voltaje."
            ),
            "paso a paso": (
                "Motor paso a paso (stepper): movimiento preciso por pasos. "
                "Tipos: unipolares y bipolares. "
                "Drivers: A4988, DRV8825, ULN2003. "
                "Ideal para CNC, impresoras 3D, brazos robóticos."
            ),
            "servo": (
                "Servo motor: posición controlada por PWM (0.5ms-2.5ms). "
                "Rango típico: 0° a 180°. "
                "Ideal para brazos robóticos, timones, mecanismos de precisión. "
                "Control con Arduino: librería Servo.h."
            ),
            "bldc": (
                "Motor BLDC (brushless DC): alta eficiencia y durabilidad. "
                "Requiere ESC (Electronic Speed Controller). "
                "Ideal para drones, vehículos eléctricos, herramientas. "
                "Control: señal PWM al ESC."
            ),
        }
        tipo = parameters.get("motor_type", "").lower()
        if tipo in motores:
            result = motores[tipo]
        else:
            lista = ", ".join(motores.keys())
            result = f"Tipo no encontrado. Disponibles: {lista}"
        say(result)
        return result

    # ── Sensores comunes ─────────────────────────────────────────
    elif action == "sensor_info":
        sensores = {
            "ultrasonico": (
                "HC-SR04: mide distancia por ultrasonido. Rango: 2cm-400cm. "
                "Pines: VCC, GND, TRIG, ECHO. "
                "Distancia = (tiempo_echo * velocidad_sonido) / 2"
            ),
            "temperatura": (
                "DHT11: temperatura y humedad. Rango: 0-50°C, ±2°C. "
                "DHT22: más preciso, rango -40 a 80°C, ±0.5°C. "
                "Comunicación: protocolo single-wire."
            ),
            "infrarrojo": (
                "IR: detección de obstáculos y líneas. "
                "Módulo TCRT5000 para seguidor de línea. "
                "Salida digital (obstáculo sí/no) o analógica (distancia)."
            ),
            "acelerometro": (
                "MPU-6050: acelerómetro + giroscopio 6 ejes. "
                "Comunicación I2C, dirección 0x68. "
                "Ideal para drones, control de gestos, estabilización."
            ),
            "encoder": (
                "Encoder rotativo: mide posición y velocidad angular. "
                "Tipos: incremental y absoluto. "
                "Pulsos por revolución (PPR) determina la resolución."
            ),
        }
        tipo = parameters.get("sensor_type", "").lower()
        if tipo in sensores:
            result = sensores[tipo]
        else:
            lista = ", ".join(sensores.keys())
            result = f"Sensor no encontrado. Disponibles: {lista}"
        say(result)
        return result

    # ── Arduino / PLC básico ─────────────────────────────────────
    elif action == "arduino":
        temas = {
            "pwm": (
                "PWM en Arduino: analogWrite(pin, valor) donde valor va de 0 a 255. "
                "Pines PWM en UNO: 3, 5, 6, 9, 10, 11. "
                "Frecuencia por defecto: ~490Hz (pines 3,9,10,11) y ~980Hz (pines 5,6)."
            ),
            "i2c": (
                "I2C en Arduino: Wire.h. SDA=A4, SCL=A5 en UNO. "
                "Wire.begin(); Wire.beginTransmission(addr); "
                "Wire.write(dato); Wire.endTransmission();"
            ),
            "spi": (
                "SPI en Arduino: SPI.h. Pines: MOSI=11, MISO=12, SCK=13, SS=10. "
                "SPI.begin(); SPI.transfer(dato);"
            ),
            "interrupcion": (
                "Interrupciones en Arduino: attachInterrupt(digitalPinToInterrupt(pin), ISR, modo). "
                "Modos: RISING, FALLING, CHANGE. "
                "Pines en UNO: 2 y 3."
            ),
            "watchdog": (
                "Watchdog Timer: reinicia el Arduino si se cuelga. "
                "#include <avr/wdt.h> "
                "wdt_enable(WDTO_2S); en setup. "
                "wdt_reset(); en loop para evitar reinicio."
            ),
        }
        tema = parameters.get("topic", "").lower()
        if tema in temas:
            result = temas[tema]
        else:
            lista = ", ".join(temas.keys())
            result = f"Tema no encontrado. Disponibles: {lista}"
        say(result)
        return result

    else:
        say(f"Acción de mecatrónica no reconocida: {action}")
        return f"Acción desconocida: {action}"