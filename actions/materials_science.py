# actions/materials_science.py
import math

def materials_science(parameters: dict, player=None, speak=None):
    action = parameters.get("action", "").lower().strip()

    def log(msg):
        if player:
            player.write_log(f"MATS: {msg}")

    def say(msg):
        if speak:
            speak(msg)
        log(msg)

    # Base de datos local de materiales comunes
    base_materiales = {
        "aluminio 6061-t6": {
            "nombre": "Aluminio 6061-T6 (Aleación de grado estructural)",
            "modulo_young_gpa": 68.9,
            "poisson": 0.33,
            "limite_elastico_mpa": 276.0,
            "conductividad_termica_w_mk": 167.0,
            "alfa_termico_10_6": 23.6,
            "densidad_kg_m3": 2700.0
        },
        "acero aisi 1020": {
            "nombre": "Acero Estructural AISI 1020 (Bajo carbono)",
            "modulo_young_gpa": 200.0,
            "poisson": 0.29,
            "limite_elastico_mpa": 350.0,
            "conductividad_termica_w_mk": 51.9,
            "alfa_termico_10_6": 11.7,
            "densidad_kg_m3": 7870.0
        },
        "cobre": {
            "nombre": "Cobre Puro (Electrolítico, recocido)",
            "modulo_young_gpa": 117.0,
            "poisson": 0.34,
            "limite_elastico_mpa": 70.0,
            "conductividad_termica_w_mk": 401.0,
            "alfa_termico_10_6": 16.5,
            "densidad_kg_m3": 8960.0
        },
        "silicio": {
            "nombre": "Silicio Monocristalino (Semiconductor base)",
            "modulo_young_gpa": 130.0,
            "poisson": 0.28,
            "limite_elastico_mpa": 120.0,
            "conductividad_termica_w_mk": 149.0,
            "alfa_termico_10_6": 2.6,
            "densidad_kg_m3": 2330.0
        },
        "titanio grado 5": {
            "nombre": "Titanio Grado 5 (Ti-6Al-4V, alta resistencia)",
            "modulo_young_gpa": 114.0,
            "poisson": 0.34,
            "limite_elastico_mpa": 880.0,
            "conductividad_termica_w_mk": 6.7,
            "alfa_termico_10_6": 8.6,
            "densidad_kg_m3": 4430.0
        }
    }

    # ── 1. Esfuerzo y Deformación Mecánica ────────────────────────
    if action == "esfuerzo_deformacion":
        load = parameters.get("load")                  # Fuerza en N
        area = parameters.get("area")                  # Área de sección transversal
        area_unit = parameters.get("area_unit", "mm2").lower().strip() # "mm2" o "m2"
        length = parameters.get("length")              # Longitud inicial L0
        delta_length = parameters.get("delta_length")  # Cambio en longitud dL
        length_unit = parameters.get("length_unit", "mm").lower().strip() # "mm" o "m"
        young_modulus = parameters.get("young_modulus") # E en GPa

        results = []
        stress = None
        strain = None

        # 1. Calcular Esfuerzo (Stress = F / A) en MPa
        if load is not None and area is not None and float(area) > 0:
            load = float(load)
            area = float(area)
            if area_unit == "m2":
                stress = (load / area) / 1e6 # Pa a MPa
            else:
                stress = load / area         # N/mm2 = MPa
            results.append(f"Esfuerzo mecánico (σ): {stress:.4f} MPa")

        # 2. Calcular Deformación Unitaria (Strain = dL / L0) (adimensional)
        if length is not None and delta_length is not None and float(length) > 0:
            length = float(length)
            delta_length = float(delta_length)
            # Como es una relación, si las unidades coinciden da igual la conversión
            strain = delta_length / length
            results.append(f"Deformación unitaria (ε): {strain:.6e} (o {strain*100:.4f}%)")

        # 3. Deducir valores usando el Módulo de Young (E) si está disponible
        if young_modulus is not None:
            E_pa = float(young_modulus) * 1e9 # GPa a Pa
            E_mpa = float(young_modulus) * 1e3 # GPa a MPa
            
            if stress is not None and strain is None:
                strain = stress / E_mpa
                results.append(f"Deformación deducida por Ley de Hooke (ε): {strain:.6e} ({strain*100:.4f}%)")
                if length is not None:
                    delta_length = strain * float(length)
                    results.append(f"Deformación total deducida (ΔL): {delta_length:.4f} {length_unit}")
            elif strain is not None and stress is None:
                stress = E_mpa * strain
                results.append(f"Esfuerzo deducido por Ley de Hooke (σ): {stress:.4f} MPa")
                if area is not None:
                    area_val = float(area)
                    if area_unit == "m2":
                        load_deduced = (stress * 1e6) * area_val
                    else:
                        load_deduced = stress * area_val # MPa * mm2 = N
                    results.append(f"Carga estimada deducida (F): {load_deduced:.2f} N")

        if not results:
            say("Necesito al menos fuerza y área para calcular esfuerzo, o longitudes para deformación unitaria.")
            return "Faltan parámetros mecánicos."
        
        result_str = " | ".join(results)
        say(result_str)
        return result_str

    # ── 2. Dilatación y Esfuerzo Térmico ──────────────────────────
    elif action == "esfuerzo_termico":
        alpha = parameters.get("alpha")             # Coeficiente lineal x 10^-6 / °C
        delta_temp = parameters.get("delta_temp")   # Cambio de temperatura en °C
        young_modulus = parameters.get("young_modulus") # E en GPa
        length = parameters.get("length")           # Longitud inicial L0 en mm o m
        length_unit = parameters.get("length_unit", "m")

        if alpha is None or delta_temp is None:
            say("Necesito el coeficiente de expansión (alpha) y el cambio de temperatura (delta_temp).")
            return "Faltan parámetros térmicos."

        alpha_val = float(alpha) * 1e-6
        dT = float(delta_temp)

        # Deformación térmica libre
        thermal_strain = alpha_val * dT
        results = [f"Deformación térmica libre (ε_th): {thermal_strain:.6e}"]

        # Dilatación lineal libre si se proporciona longitud
        if length is not None:
            dL_th = thermal_strain * float(length)
            results.append(f"Dilatación libre (ΔL_th): {dL_th:.4f} {length_unit}")

        # Esfuerzo térmico si el material está totalmente restringido (empotrado)
        if young_modulus is not None:
            E_mpa = float(young_modulus) * 1e3 # GPa a MPa
            thermal_stress = E_mpa * thermal_strain
            results.append(f"Esfuerzo térmico restringido (σ_th): {abs(thermal_stress):.4f} MPa ({'Compresión' if dT > 0 else 'Tracción'})")

        result_str = " | ".join(results)
        say(result_str)
        return result_str

    # ── 3. Base de Datos de Materiales ─────────────────────────────
    elif action == "seleccion_materials" or action == "seleccion_materiales":
        mat_query = parameters.get("material_name", "").lower().strip()
        
        if not mat_query:
            lista = ", ".join(m.title() for m in base_materiales.keys())
            result = f"Materiales disponibles en la base de datos local:\n{lista}\nEspecifique 'material_name' para ver sus propiedades."
            say(result)
            return result

        # Búsqueda aproximada
        found_mat = None
        for key, value in base_materiales.items():
            if mat_query in key:
                found_mat = value
                break

        if found_mat:
            result = (
                f"Propiedades de {found_mat['nombre']}:\n"
                f"  - Módulo de Elasticidad (Young): {found_mat['modulo_young_gpa']:.1f} GPa\n"
                f"  - Relación de Poisson (ν): {found_mat['poisson']:.2f}\n"
                f"  - Límite Elástico de Fluencia: {found_mat['limite_elastico_mpa']:.1f} MPa\n"
                f"  - Coeficiente de Dilatación Térmica (α): {found_mat['alfa_termico_10_6']:.1f} x 10^-6 /°C\n"
                f"  - Conductividad Térmica: {found_mat['conductividad_termica_w_mk']:.1f} W/m·K\n"
                f"  - Densidad (ρ): {found_mat['densidad_kg_m3']:.1f} kg/m³"
            )
        else:
            lista = ", ".join(m.title() for m in base_materiales.keys())
            result = f"Material '{mat_query}' no hallado. Disponibles: {lista}"
        
        say(result)
        return result

    else:
        say(f"Acción de ciencia de materiales no reconocida: {action}")
        return f"Acción desconocida: {action}"
