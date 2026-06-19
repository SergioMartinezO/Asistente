# Arquitectura modular REX (alta funcionalidad)

Este documento describe la nueva capa modular creada en `assistant_modules/`.

## Módulos implementados

1. **Core Engine** (`assistant_modules/core_engine`)
   - NLP en español (`nlp.py`)
   - Motor de razonamiento por reglas REX (`reasoning.py`)
   - Gestión de memoria y preferencias (`memory.py`)

2. **Comunicación** (`assistant_modules/communication`)
   - Texto unificado para consola/VS Code/web (`text_interface.py`)
   - Voz STT/TTS (stub desacoplado) (`voice_interface.py`)
   - Puente multimodal para visión futura (`multimodal.py`)

3. **Electrónica** (`assistant_modules/electronics/module.py`)
   - Ley de Ohm
   - Frecuencia de corte RC
   - Conversión dBm↔mW, Vrms↔Vpp
   - Solver básico nodal/mallas 2x2
   - Simulación divisor de tensión

4. **Sistemas y Software** (`assistant_modules/software_systems/module.py`)
   - Generación base de snippets (Python/C/C++/Java/JS)
   - Sugerencias de Big-O, UML y patrones
   - Estado de integración IDE

5. **Mecatrónica** (`assistant_modules/mechatronics/module.py`)
   - Torque, potencia mecánica, relación de transmisión
   - Sugerencias de control de motores
   - Referencias de enlace con Arduino/PLC/MCU

6. **Telecomunicaciones** (`assistant_modules/telecommunications/module.py`)
   - Tasa de Nyquist
   - Capacidad de Shannon
   - Pérdida de espacio libre (FSPL)
   - Referencias de protocolos y modulación

7. **Matemático** (`assistant_modules/mathematics/module.py`)
   - Derivada numérica, integración trapezoidal
   - Sistema lineal 2x2
   - Paso Euler para ODE
   - Helpers para Laplace/Fourier
   - Números complejos y fasores

8. **Automatización y Workflow** (`assistant_modules/automation_workflow/module.py`)
   - Checklist estructurado
   - Plantilla de script
   - Estado de integraciones GitHub/OneDrive/FS
   - Generación de informe técnico

9. **Seguridad y Control** (`assistant_modules/security_control/module.py`)
   - Chequeo de permisos
   - Redacción de datos sensibles en texto
   - Mensaje de cierre seguro

## Arquitectura transversal implementada

- **Frontend**: `assistant_modules/frontend/interfaces.py`
- **Backend (fachada)**: `assistant_modules/backend/facade.py`
- **Integraciones**: `assistant_modules/integrations/connectors.py`
- **Persistencia**: `assistant_modules/persistence/store.py`

## Uso mínimo

```python
from assistant_modules import RexAssistantBackend

backend = RexAssistantBackend()
resp = backend.process_text("Calcula ley de ohm para 12V y 6 ohm")
print(resp.intent, resp.action, resp.data)
```

## Nota de compatibilidad

Esta capa es **desacoplada** del flujo actual de `main.py/controller.py` para no romper la ejecución existente. Se puede integrar gradualmente como backend principal.
