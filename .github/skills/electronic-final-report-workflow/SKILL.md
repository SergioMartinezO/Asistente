---
name: electronic-final-report-workflow
description: 'Genera un informe técnico final de diseño y validación electrónica con estructura profesional, tablas de resultados, conclusiones, riesgos residuales y siguientes pasos, manteniendo explicación continua y avance en tiempo real.'
argument-hint: 'Proyecto, versión, objetivos, requisitos clave, resultados de simulación/pruebas, hallazgos y destinatario del informe.'
user-invocable: true
disable-model-invocation: false
---

# Flujo de Informe Técnico Final Electrónico (sin cortes)

## Cuándo usar
- Cuando el diseño y/o validación ya tienen resultados y se necesita cierre documental.
- Cuando el usuario necesita un reporte profesional para cliente, comité técnico o auditoría interna.
- Cuando se requiere trazabilidad entre requisitos, resultados y conclusiones.

## Resultado esperado
- Informe final estructurado y listo para compartir.
- Resumen ejecutivo + anexos técnicos con evidencia.
- Estado de cumplimiento por requisito y riesgos residuales documentados.

## Reglas de comunicación obligatorias
1. Nunca interrumpir la explicación; siempre cerrar con siguiente paso concreto.
2. Reportar avance en tiempo real con formato fijo:
   - `Fase X/Y: <nombre>`
   - `Estado: en curso | completada | bloqueada`
   - `Avance: <0-100>%`
   - `Siguiente acción: <acción concreta>`
3. Diferenciar claramente: hechos medidos vs interpretación técnica.
4. Si faltan datos, declarar supuestos y marcar impacto en la conclusión.

## Procedimiento

### Fase 1/8 — Definir objetivo y audiencia del informe
- Identificar destinatario (técnico, gerencial, cliente final).
- Ajustar profundidad técnica y nivel de detalle.
- Establecer alcance de la versión reportada.

**Checklist de cierre**
- [ ] Audiencia definida
- [ ] Alcance/versionado definido
- [ ] Propósito del informe claro

### Fase 2/8 — Consolidar entradas y evidencias
- Reunir: requisitos, BOM, esquemático, resultados de simulación, plan de pruebas y bitácora.
- Verificar integridad de evidencias (tablas, capturas, observaciones, fechas).

**Checklist de cierre**
- [ ] Evidencias centralizadas
- [ ] Fuentes verificadas
- [ ] Huecos de información identificados

### Fase 3/8 — Estructurar trazabilidad
- Construir matriz `Requisito -> Método de validación -> Resultado -> Cumplimiento`.
- Clasificar cumplimiento: `Cumple`, `Cumple parcial`, `No cumple`, `No evaluado`.

**Checklist de cierre**
- [ ] Matriz de trazabilidad completa
- [ ] Criterios de clasificación explícitos
- [ ] Casos críticos resaltados

### Fase 4/8 — Redactar resultados técnicos
- Presentar resultados por bloque funcional o por requisito.
- Incluir condiciones de medición/simulación y unidad de cada métrica.
- Comparar valor esperado vs valor obtenido.

**Checklist de cierre**
- [ ] Resultados cuantitativos documentados
- [ ] Condiciones de ensayo incluidas
- [ ] Diferencias respecto al objetivo explicadas

### Fase 5/8 — Analizar desviaciones y causa raíz
- Explicar fallas o desvíos relevantes con hipótesis y evidencia.
- Indicar impacto en seguridad, desempeño, costo y cronograma.

**Branching recomendado**
- Si el desvío compromete seguridad: priorizar mitigación inmediata y bloqueo de liberación.
- Si el desvío es menor: documentar workaround y plan de mejora.
- Si faltan datos: declarar límite de validez de conclusiones.

**Checklist de cierre**
- [ ] Desviaciones priorizadas
- [ ] Causa raíz (o hipótesis) documentada
- [ ] Impacto técnico cuantificado

### Fase 6/8 — Conclusiones y estado final
- Emitir conclusión por requisito y conclusión global del proyecto.
- Declarar si el diseño está listo para piloto/producción/revisión adicional.

**Checklist de cierre**
- [ ] Conclusión por requisito
- [ ] Conclusión global sustentada
- [ ] Estado de liberación recomendado

### Fase 7/8 — Riesgos residuales y plan de acción
- Listar riesgos abiertos con severidad/probabilidad.
- Definir acciones, responsable y fecha objetivo.

**Checklist de cierre**
- [ ] Riesgos residuales listados
- [ ] Plan de acción asignado
- [ ] Prioridades definidas

### Fase 8/8 — Formato final y entrega
- Generar versión final con índice, numeración y anexos.
- Verificar consistencia terminológica y unidades.
- Preparar versión corta (1 página) y versión completa (técnica).

**Checklist de cierre**
- [ ] Informe final consistente
- [ ] Resumen ejecutivo incluido
- [ ] Anexos técnicos referenciados

## Estructura recomendada del informe
1. Portada y metadatos (proyecto, versión, fecha, autor)
2. Resumen ejecutivo
3. Alcance y objetivos
4. Requisitos y criterios de aceptación
5. Metodología (simulación/pruebas)
6. Resultados y trazabilidad
7. Desviaciones y causa raíz
8. Conclusiones
9. Riesgos residuales
10. Plan de acción y próximos pasos
11. Anexos (tablas completas, gráficos, evidencias)

## Plantillas mínimas (copiar y completar)

### Tabla de cumplimiento por requisito
- `ID requisito | Objetivo | Método | Resultado obtenido | Estado | Evidencia`

### Registro de riesgo residual
- `ID riesgo | Descripción | Severidad | Probabilidad | Mitigación | Responsable | Fecha`

### Resumen ejecutivo (5 líneas)
- Contexto del proyecto
- Estado general de cumplimiento
- Principal hallazgo técnico
- Riesgo más relevante
- Recomendación de siguiente fase

## Formato de actualización en tiempo real
En cada respuesta, usar:
1. `Fase X/Y: ...`
2. `Estado: ...`
3. `Avance: ...%`
4. `Qué se completó:`
5. `Qué sigue ahora:`
6. `Riesgos o supuestos:`

## Configuración por defecto
- **Ámbito**: workspace.
- **Compatibilidad**: se integra con `electronic-component-design-workflow` y `electronic-test-plan-workflow`.
- **Criterio anti-corte**: no cerrar respuesta sin siguiente acción concreta.

## Entradas recomendadas
- Nombre del proyecto y versión.
- Lista de requisitos y umbrales de aceptación.
- Resultados de simulación y/o pruebas con evidencia.
- Hallazgos, incidencias y correcciones aplicadas.
- Destinatario y formato esperado del informe.

## Salidas mínimas esperadas
- Informe técnico estructurado y trazable.
- Tabla de cumplimiento por requisito.
- Riesgos residuales con plan de acción.
- Conclusión global y recomendación de siguiente etapa.
