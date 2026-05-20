import math

def electronics(parameters: dict, player=None, speak=None):
    action = parameters.get("action", "").lower()
    
    def log(msg):
        if player:
            player.write_log(f"ELEC: {msg}")
    
    def say(msg):
        if speak:
            speak(msg)
        log(msg)

    # ── Ley de Ohm ──────────────────────────────────────────────
    if action == "ohm":
        v = parameters.get("voltage")
        i = parameters.get("current")
        r = parameters.get("resistance")
        p = parameters.get("power")
        results = []
        if v is not None and i is not None:
            r = v / i
            p = v * i
            results = [f"Resistencia: {r:.4f} Ω", f"Potencia: {p:.4f} W"]
        elif v is not None and r is not None:
            i = v / r
            p = v ** 2 / r
            results = [f"Corriente: {i:.4f} A", f"Potencia: {p:.4f} W"]
        elif i is not None and r is not None:
            v = i * r
            p = i ** 2 * r
            results = [f"Voltaje: {v:.4f} V", f"Potencia: {p:.4f} W"]
        elif p is not None and r is not None:
            v = math.sqrt(p * r)
            i = math.sqrt(p / r)
            results = [f"Voltaje: {v:.4f} V", f"Corriente: {i:.4f} A"]
        else:
            say("Necesito al menos dos valores: voltaje, corriente, resistencia o potencia.")
            return "Faltan parámetros para Ley de Ohm."
        result = " | ".join(results)
        say(result)
        return result

    # ── Resistencias en serie y paralelo ────────────────────────
    elif action in ("serie", "paralelo"):
        values = parameters.get("values", [])
        if not values:
            say("Necesito una lista de resistencias.")
            return "Sin valores."
        values = [float(v) for v in values]
        if action == "serie":
            total = sum(values)
            result = f"Resistencia total en serie: {total:.4f} Ω"
        else:
            total = 1 / sum(1/v for v in values)
            result = f"Resistencia total en paralelo: {total:.4f} Ω"
        say(result)
        return result

    # ── Divisor de tensión ───────────────────────────────────────
    elif action == "divisor_tension":
        vin  = float(parameters.get("vin", 0))
        r1   = float(parameters.get("r1", 0))
        r2   = float(parameters.get("r2", 0))
        vout = vin * r2 / (r1 + r2)
        result = f"Vout = {vout:.4f} V (Vin={vin}V, R1={r1}Ω, R2={r2}Ω)"
        say(result)
        return result

    # ── Reactancia capacitiva ────────────────────────────────────
    elif action == "reactancia_c":
        f = float(parameters.get("frequency", 0))
        c = float(parameters.get("capacitance", 0))
        if f == 0 or c == 0:
            say("Necesito frecuencia en Hz y capacitancia en Faradios.")
            return "Faltan parámetros."
        xc = 1 / (2 * math.pi * f * c)
        result = f"Reactancia capacitiva Xc = {xc:.4f} Ω (f={f}Hz, C={c}F)"
        say(result)
        return result

    # ── Reactancia inductiva ─────────────────────────────────────
    elif action == "reactancia_l":
        f = float(parameters.get("frequency", 0))
        l = float(parameters.get("inductance", 0))
        if f == 0 or l == 0:
            say("Necesito frecuencia en Hz e inductancia en Henrios.")
            return "Faltan parámetros."
        xl = 2 * math.pi * f * l
        result = f"Reactancia inductiva XL = {xl:.4f} Ω (f={f}Hz, L={l}H)"
        say(result)
        return result

    # ── Frecuencia de corte RC/RL ────────────────────────────────
    elif action == "frecuencia_corte":
        r = float(parameters.get("resistance", 0))
        c = parameters.get("capacitance")
        l = parameters.get("inductance")
        if c:
            fc = 1 / (2 * math.pi * r * float(c))
            result = f"Frecuencia de corte RC: fc = {fc:.4f} Hz (R={r}Ω, C={c}F)"
        elif l:
            fc = r / (2 * math.pi * float(l))
            result = f"Frecuencia de corte RL: fc = {fc:.4f} Hz (R={r}Ω, L={l}H)"
        else:
            say("Necesito R y C, o R y L.")
            return "Faltan parámetros."
        say(result)
        return result

    # ── Conversión dBm ↔ mW ──────────────────────────────────────
    elif action == "dbm_mw":
        dbm = parameters.get("dbm")
        mw  = parameters.get("mw")
        if dbm is not None:
            mw_val = 10 ** (float(dbm) / 10)
            result = f"{dbm} dBm = {mw_val:.4f} mW"
        elif mw is not None:
            dbm_val = 10 * math.log10(float(mw))
            result = f"{mw} mW = {dbm_val:.4f} dBm"
        else:
            say("Necesito un valor en dBm o mW.")
            return "Faltan parámetros."
        say(result)
        return result

    # ── Conversión Vrms ↔ Vpp ────────────────────────────────────
    elif action == "vrms_vpp":
        vrms = parameters.get("vrms")
        vpp  = parameters.get("vpp")
        if vrms is not None:
            vpp_val  = float(vrms) * 2 * math.sqrt(2)
            vpico    = float(vrms) * math.sqrt(2)
            result   = f"Vrms={vrms}V → Vpp={vpp_val:.4f}V | Vpico={vpico:.4f}V"
        elif vpp is not None:
            vrms_val = float(vpp) / (2 * math.sqrt(2))
            result   = f"Vpp={vpp}V → Vrms={vrms_val:.4f}V"
        else:
            say("Necesito Vrms o Vpp.")
            return "Faltan parámetros."
        say(result)
        return result

    # ── Código de colores de resistencias ────────────────────────
    elif action == "codigo_colores":
        colores = {
            "negro":0,"marrón":1,"rojo":2,"naranja":3,"amarillo":4,
            "verde":5,"azul":6,"violeta":7,"gris":8,"blanco":9
        }
        tolerancias = {
            "dorado":"±5%","plateado":"±10%","marrón":"±1%","rojo":"±2%"
        }
        bandas = parameters.get("bands", [])
        if len(bandas) < 3:
            say("Necesito al menos 3 bandas de colores.")
            return "Faltan bandas."
        bandas = [b.lower() for b in bandas]
        try:
            if len(bandas) == 4:
                val = (colores[bandas[0]] * 10 + colores[bandas[1]]) * (10 ** colores[bandas[2]])
                tol = tolerancias.get(bandas[3], "±20%")
            else:
                val = (colores[bandas[0]]*100 + colores[bandas[1]]*10 + colores[bandas[2]]) * (10 ** colores[bandas[3]])
                tol = tolerancias.get(bandas[4], "±20%")
            if val >= 1_000_000:
                display = f"{val/1_000_000:.2f} MΩ"
            elif val >= 1_000:
                display = f"{val/1_000:.2f} kΩ"
            else:
                display = f"{val} Ω"
            result = f"Resistencia: {display} {tol}"
        except KeyError as e:
            result = f"Color no reconocido: {e}"
        say(result)
        return result

    # ── Prefijos SI ──────────────────────────────────────────────
    elif action == "prefijo_si":
        prefijos = {
            "pico":1e-12,"nano":1e-9,"micro":1e-6,"mili":1e-3,
            "kilo":1e3,"mega":1e6,"giga":1e9,"tera":1e12
        }
        valor  = float(parameters.get("value", 1))
        origen = parameters.get("from_prefix", "").lower()
        destino= parameters.get("to_prefix", "base").lower()
        base   = valor * prefijos.get(origen, 1)
        final  = base / prefijos.get(destino, 1) if destino != "base" else base
        result = f"{valor} {origen} = {final:.6g} {destino}"
        say(result)
        return result

    else:
        say(f"Acción de electrónica no reconocida: {action}")
        return f"Acción desconocida: {action}"