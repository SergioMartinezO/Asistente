# Plantilla operativa — Diseño electrónico con costos, riesgos y viabilidad

Usa esta plantilla para exigir un producto electrónico completo que incluya: diseño técnico, cronograma, presupuesto (CAPEX/OPEX), riesgos, mitigaciones y KPIs de implementación.

Plantillas relacionadas:

- Índice maestro: [`plantillas_indice.md`](./plantillas_indice.md)
- Diseño técnico base: [`plantilla_prompt_diseno_electronico.md`](./plantilla_prompt_diseno_electronico.md)
- Licitación/propuesta: [`plantilla_licitacion_propuesta_electronica.md`](./plantilla_licitacion_propuesta_electronica.md)

---

## 1) Plantilla lista para copiar y pegar

Diseña un dispositivo electrónico completo, viable y ejecutable con enfoque técnico, económico y de riesgos.

### Contexto del proyecto

- **Nombre del proyecto**: [NOMBRE]
- **Objetivo funcional**: [FUNCIÓN PRINCIPAL DEL DISPOSITIVO]
- **Entorno de operación**: [INDUSTRIAL / AGRÍCOLA / DOMÉSTICO / SALUD / OTRO]
- **Usuarios objetivo**: [QUIÉNES LO USARÁN]
- **Fecha de inicio**: [YYYY-MM-DD]
- **Horizonte de implementación**: [N meses]

### Restricciones obligatorias

- **Presupuesto máximo CAPEX**: [USD]
- **Presupuesto mensual OPEX**: [USD/mes]
- **Consumo energético máximo**: [W o kWh/mes]
- **Disponibilidad esperada**: [ej. 99.5%]
- **Condiciones ambientales**: [temperatura, humedad, polvo, vibración]
- **Restricciones normativas**: [IEC, ISO, RETIE, CE, FCC, etc.]

### Entregables obligatorios

1. Plan por fases con **fecha de inicio y fin** por fase (Hardware, Software, Diagramas, Word, Web).
2. Duración por fase y ruta crítica resumida.
3. Entregables verificables por fase.
4. Lista de componentes (BOM) con:
   - costo unitario,
   - costo total,
   - proveedor sugerido,
   - justificación técnica.
5. Diseño de software con estándares de calidad (arquitectura, manejo de errores, pruebas, trazabilidad).
6. Diagramas técnicos (bloques, esquemático, flujo software).
7. Documento Word final y entregable web.
8. Matriz de riesgos con probabilidad, impacto y mitigación.
9. Evaluación de sostenibilidad:
   - consumo energético,
   - mantenibilidad,
   - impacto ambiental.
10. Evaluación de impacto social y económico (beneficios esperados, costos operativos y retorno estimado).
11. KPIs de éxito para 3, 6 y 12 meses.
12. Cierre explícito con viabilidad técnica, viabilidad económica, viabilidad operativa y recomendación final de implementación.

### Formato de salida requerido

- Respuesta estructurada por secciones numeradas.
- Tablas para cronograma, costos y riesgos.
- Fechas en formato `YYYY-MM-DD`.
- Sin texto ambiguo ni genérico.
- Confirmación final: **"Proyecto completo y listo para ejecución"**.

---

## 2) Plantilla de parámetros avanzados (opcional)

Incluye además estos parámetros cuando quieras control fino:

- **phase_durations**:
  - Hardware: [N]
  - Software: [N]
  - Diagramas: [N]
  - Word: [N]
  - Web: [N]
- **software_standards**:
  - [Estándar 1]
  - [Estándar 2]
  - [Estándar 3]
- **risk_tolerance**: [baja/media/alta]
- **contingency_budget_percent**: [5-20]
- **target_roi_months**: [N]
- **maintenance_strategy**: [preventivo/predictivo/correctivo híbrido]

---

## 3) Mini-checklist de validación (para revisar la respuesta)

Marca ✅ solo si está completo:

- [ ] Incluye fechas de inicio/fin por cada fase.
- [ ] Incluye entregables concretos por fase.
- [ ] Incluye BOM con costos y totales.
- [ ] Incluye matriz de riesgos con mitigaciones.
- [ ] Incluye KPIs de seguimiento (3/6/12 meses).
- [ ] Incluye evaluación técnica/económica/operativa.
- [ ] Cierra con recomendación y viabilidad final.

---

## 4) Ejemplo corto de uso

Diseña un sistema electrónico de monitoreo de cadena de frío para transporte farmacéutico con sensores redundantes, telemetría en tiempo real y alertas de desviación térmica.

CAPEX máximo: 1200 USD
OPEX mensual máximo: 90 USD
Inicio: 2026-07-15
Disponibilidad objetivo: 99.7%

Entrega cronograma por fases con fechas, costos detallados, riesgos y mitigaciones, KPIs de 3/6/12 meses y confirmación de viabilidad técnica, económica y operativa.
