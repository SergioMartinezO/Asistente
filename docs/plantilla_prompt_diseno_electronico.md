# Plantilla operativa — Diseño de dispositivo electrónico completo

Usa esta plantilla cuando quieras que el asistente entregue un proyecto **completo, viable y estructurado** (hardware + software + diagramas + Word + Web), con cronograma por fases y entregables.

Plantillas relacionadas:

- Índice maestro: [`plantillas_indice.md`](./plantillas_indice.md)
- Versión con costos/riesgos: [`plantilla_prompt_diseno_electronico_costos_riesgos.md`](./plantilla_prompt_diseno_electronico_costos_riesgos.md)
- Versión licitación/comercial: [`plantilla_licitacion_propuesta_electronica.md`](./plantilla_licitacion_propuesta_electronica.md)

---

## 1) Plantilla rápida (copiar y pegar)

Diseña un dispositivo electrónico completo y viable para el siguiente caso:

- **Nombre del proyecto**: [NOMBRE]
- **Objetivo funcional**: [QUÉ DEBE HACER EL DISPOSITIVO]
- **Usuario/entorno de uso**: [DÓNDE Y PARA QUIÉN]
- **Restricciones técnicas**: [energía, tamaño, conectividad, seguridad, costo]
- **Fecha de inicio del proyecto**: [YYYY-MM-DD]

### Requisitos obligatorios de salida

1. **Plan por fases con fechas de inicio y fin** (Hardware, Software, Diagramas, Word, Web).
2. **Duración por fase** en días.
3. **Entregables por fase** (claros y verificables).
4. **Lista de componentes** con especificación técnica y justificación.
5. **Código fuente** comentado en español y con estándares de desarrollo de software.
6. **Diagramas técnicos** (bloques, circuito esquemático y flujo software).
7. **Documento Word final** y **entregable web HTML**.
8. Confirmación final de **viabilidad** en:
   - estructuración,
   - implementación,
   - ejecución.

Además, confirma explícitamente al final: **"Proyecto completo y listo para ejecución"**.

---

## 2) Plantilla avanzada (control fino del cronograma)

Diseña un dispositivo electrónico completo y genera los entregables técnicos con los siguientes parámetros:

- **project_title**: [NOMBRE]
- **overview**: [RESUMEN FUNCIONAL]
- **project_start_date**: [YYYY-MM-DD]
- **phase_durations**:
  - Hardware: [N días]
  - Software: [N días]
  - Diagramas: [N días]
  - Word: [N días]
  - Web: [N días]
- **software_standards**:
  - [Estándar 1]
  - [Estándar 2]
  - [Estándar 3]
- **components**:
  - nombre: [Componente 1]
    especificacion: [Especificación técnica]
    justificacion: [Justificación de ingeniería]
  - nombre: [Componente 2]
    especificacion: [...]
    justificacion: [...]

### Validaciones exigidas

- No respuestas vagas.
- Cada fase debe tener inicio, fin, duración y entregables.
- El software debe cumplir estándares de calidad explícitos.
- Debe cerrar con resumen de artefactos generados (Word, Web, código y diagramas).

---

## 3) Ejemplo listo para usar

Diseña un dispositivo electrónico completo y viable para monitoreo de temperatura y control de ventilación en invernadero.

- Nombre del proyecto: Control Inteligente de Invernadero
- Objetivo funcional: medir temperatura/humedad y activar ventilación automáticamente, con registro y visualización.
- Usuario/entorno: productor agrícola, operación 24/7 en ambiente húmedo.
- Restricciones: alimentación 12V, bajo consumo, costo máximo 180 USD, conectividad WiFi.
- Fecha de inicio del proyecto: 2026-07-10

Requisitos obligatorios de salida:

1) Plan por fases con inicio/fin (Hardware, Software, Diagramas, Word, Web).
2) Duración por fase y entregables verificables.
3) Componentes con especificación/justificación.
4) Código comentado en español con estándares de calidad.
5) Diagramas técnicos completos.
6) Entregable Word y Web.
7) Confirmación de viabilidad técnica y de ejecución.
8) Cierre con: "Proyecto completo y listo para ejecución".
