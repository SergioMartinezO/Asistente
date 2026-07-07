# Índice maestro de plantillas — Proyectos electrónicos

Este índice centraliza las plantillas disponibles para solicitar diseños y propuestas de forma consistente, estructurada y profesional.

---

## Inicio rápido

Si es la primera vez que usarás estas plantillas, revisa primero:

- `docs/guia_uso_plantillas.md`

---

## Plantillas disponibles

### 0) Plantilla ultra-corta (comando rápido)

- Archivo: [`plantilla_ultracorta_diseno_electronico.md`](./plantilla_ultracorta_diseno_electronico.md)
- Úsala cuando necesitas:
  - pedir un diseño completo en menos de 1 minuto,
  - mantener estructura mínima obligatoria,
  - lanzar solicitudes rápidas por texto o voz.

### 1) Diseño técnico completo (base)

- Archivo: [`plantilla_prompt_diseno_electronico.md`](./plantilla_prompt_diseno_electronico.md)
- Úsala cuando necesitas:
  - diseño integral (hardware + software + diagramas + Word + Web),
  - cronograma por fases con fechas,
  - entregables técnicos claros,
  - validación de viabilidad técnica.

### 2) Diseño con costos, riesgos y KPIs

- Archivo: [`plantilla_prompt_diseno_electronico_costos_riesgos.md`](./plantilla_prompt_diseno_electronico_costos_riesgos.md)
- Úsala cuando necesitas además:
  - CAPEX/OPEX,
  - matriz de riesgos y mitigaciones,
  - evaluación social/económica,
  - KPIs de seguimiento (3/6/12 meses).

### 3) Licitación / propuesta comercial técnica

- Archivo: [`plantilla_licitacion_propuesta_electronica.md`](./plantilla_licitacion_propuesta_electronica.md)
- Úsala cuando necesitas:
  - documento tipo pre-venta o licitación,
  - alcance/exclusiones/supuestos,
  - SLA, garantías y soporte,
  - condiciones comerciales y cierre ejecutivo.

---

## Skills operativos disponibles (workflows)

Además de las plantillas, este repositorio incluye skills ejecutables para flujo técnico de punta a punta:

### A) Diseño de componente electrónico

- Archivo: [`SKILL.md`](../.github/skills/electronic-component-design-workflow/SKILL.md)
- Comando: `/electronic-component-design-workflow`
- Úsalo para:
  - levantar requisitos,
  - seleccionar materiales y arquitectura,
  - diseñar y simular sin cortes,
  - reportar avance en tiempo real.

### B) Plan de pruebas electrónico

- Archivo: [`SKILL.md`](../.github/skills/electronic-test-plan-workflow/SKILL.md)
- Comando: `/electronic-test-plan-workflow`
- Úsalo para:
  - construir matriz de trazabilidad,
  - ejecutar validaciones PASS/FAIL,
  - documentar evidencias y fallas,
  - iterar correcciones con criterios claros.

### C) Reporte técnico final

- Archivo: [`SKILL.md`](../.github/skills/electronic-final-report-workflow/SKILL.md)
- Comando: `/electronic-final-report-workflow`
- Úsalo para:
  - consolidar resultados,
  - emitir conclusiones por requisito,
  - registrar riesgos residuales,
  - entregar informe final profesional.

### D) Orquestador maestro 1-click

- Archivo: [`SKILL.md`](../.github/skills/electronic-master-orchestrator-workflow/SKILL.md)
- Comando: `/electronic-master-orchestrator-workflow`
- Úsalo para:
  - ejecutar diseño → pruebas → reporte en una sola invocación,
  - aplicar compuertas de calidad G1..G4,
  - mantener continuidad de explicación y avance en tiempo real.

### Comparativa rápida de skills

| Skill | Objetivo principal | Entrada mínima recomendada | Salida esperada | Cuándo usar |
| --- | --- | --- | --- | --- |
| `/electronic-component-design-workflow` | Diseñar componente/circuito con criterios técnicos claros | Tipo de componente, especificaciones eléctricas, restricciones | Arquitectura, BOM preliminar, esquema/cálculos, simulación inicial | Inicio del proyecto o rediseño técnico |
| `/electronic-test-plan-workflow` | Validar desempeño con trazabilidad y evidencia | Requisitos con umbrales, entorno de prueba, instrumentos disponibles | Matriz requisito→prueba, resultados PASS/FAIL, hallazgos y acciones | Cuando el diseño ya puede verificarse |
| `/electronic-final-report-workflow` | Cerrar documentalmente con informe técnico profesional | Resultados de diseño/pruebas, destinatario, versión del proyecto | Informe final, conclusiones por requisito, riesgos residuales y plan de acción | Cierre técnico para cliente/comité/auditoría |
| `/electronic-master-orchestrator-workflow` | Ejecutar flujo completo 1-click (diseño→pruebas→reporte) | Objetivo global, restricciones, métricas de éxito, contexto del proyecto | Paquete end-to-end con compuertas G1..G4 y entrega final trazable | Cuando se requiere punta a punta sin fragmentar trabajo |

---

## Comparativa rápida

| Plantilla | Mejor para | Incluye cronograma | Incluye costos/riesgos | Incluye SLA/garantías |
| --- | --- | --- | --- | --- |
| 1) Diseño técnico base | Diseño e implementación técnica | ✅ | ⚪ (básico) | ❌ |
| 2) Costos y riesgos | Viabilidad financiera/operativa | ✅ | ✅ | ❌ |
| 3) Licitación comercial | Propuesta formal a cliente | ✅ | ✅ | ✅ |

---

## Guía rápida de selección

- Si el objetivo es **diseñar y construir** el producto: usa **Plantilla 1**.
- Si además debes **justificar inversión y controlar riesgos**: usa **Plantilla 2**.
- Si debes **presentar oferta formal a cliente/entidad**: usa **Plantilla 3**.

---

## Recomendación de flujo en proyectos reales

1. Inicia con **Plantilla 1** para consolidar arquitectura técnica.
2. Evoluciona a **Plantilla 2** para validar viabilidad financiera y operativa.
3. Finaliza con **Plantilla 3** para empaquetar la propuesta comercial formal.

Si quieres operación guiada y secuencial automática, usa directamente:

1. **Orquestador maestro**: `/electronic-master-orchestrator-workflow`.

---

## Nota de calidad

Para máxima consistencia en las respuestas, siempre define:

- fecha de inicio (`YYYY-MM-DD`),
- restricciones de costo y energía,
- nivel de detalle de entregables,
- criterios de aceptación por fase.
