---
name: electronic-test-plan-workflow
description: 'Genera y ejecuta un plan de pruebas para componentes/circuitos electrónicos con criterios de aceptación, trazabilidad, evidencias y reporte continuo de avance (sin cortes).'
argument-hint: 'Componente/circuito, requisitos eléctricos, entorno, normas aplicables, instrumentos disponibles y prioridad de riesgo.'
user-invocable: true
disable-model-invocation: false
---

# Flujo de Plan de Pruebas Electrónicas (sin cortes)

## Cuándo usar
- Cuando el diseño ya tiene esquema/simulación preliminar y se necesita validar desempeño real.
- Cuando el usuario requiere una estrategia clara de verificación con resultados reproducibles.
- Cuando se necesita seguimiento de progreso en tiempo real durante validación.

## Objetivo
Definir, ejecutar y documentar un plan de pruebas con:
- matriz de pruebas trazable a requisitos,
- criterios PASS/FAIL explícitos,
- evidencia técnica (mediciones, tablas, observaciones),
- cierre con acciones correctivas y riesgos residuales.

## Reglas de comunicación obligatorias
1. Nunca cortar la explicación: cerrar siempre con próximo paso inmediato.
2. Reportar progreso por fase usando:
   - `Fase X/Y: <nombre>`
   - `Estado: en curso | completada | bloqueada`
   - `Avance: <0-100>%`
   - `Siguiente acción: <acción concreta>`
3. Cada fase debe incluir checklist de cierre.
4. Si faltan datos, continuar con supuestos explícitos y marcar impacto/riesgo.

## Procedimiento

### Fase 1/8 — Alcance y criterios de éxito
- Enumerar requisitos funcionales y no funcionales a validar.
- Definir variables críticas: precisión, eficiencia, ruido, temperatura, estabilidad, seguridad.
- Acordar umbrales de aceptación por requisito.

**Checklist de cierre**
- [ ] Requisitos priorizados
- [ ] Criterios de aceptación definidos
- [ ] Riesgos críticos identificados

### Fase 2/8 — Matriz de trazabilidad
- Crear matriz: `ID requisito -> caso de prueba -> métrica -> umbral -> evidencia`.
- Asignar prioridad: alta/media/baja según riesgo técnico.

**Checklist de cierre**
- [ ] Cobertura de requisitos >= 95%
- [ ] Casos críticos marcados
- [ ] Métricas y unidades definidas

### Fase 3/8 — Estrategia de prueba
- Definir tipos de prueba: funcional, estrés, térmica, transitorio, EMC/ruido (si aplica), seguridad.
- Elegir orden de ejecución para minimizar riesgo temprano.

**Branching recomendado**
- Si potencia elevada: iniciar por seguridad eléctrica y térmica.
- Si señal sensible: iniciar por ruido, estabilidad y sensibilidad a tolerancias.
- Si costo/tiempo limitados: ejecutar primero pruebas de mayor riesgo e impacto.

**Checklist de cierre**
- [ ] Tipos de prueba seleccionados
- [ ] Secuencia de ejecución definida
- [ ] Criterio de abortar/repetir documentado

### Fase 4/8 — Preparación de entorno e instrumentación
- Definir banco de prueba: fuentes, cargas, osciloscopio, multímetro, analizador, cámara térmica, etc.
- Definir calibración/estado de instrumentos.
- Establecer formato de captura de datos y evidencias.

**Checklist de cierre**
- [ ] Instrumentos disponibles y verificados
- [ ] Procedimientos de medición definidos
- [ ] Plantilla de registro preparada

### Fase 5/8 — Simulación de verificación previa
- Ejecutar verificación previa en simulación (preferencia: Proteus, o herramienta disponible).
- Validar casos nominales y extremos para reducir iteraciones de laboratorio.

**Checklist de cierre**
- [ ] Casos nominal/extremos simulados
- [ ] Desviaciones frente a requisitos identificadas
- [ ] Ajustes previos a prototipo recomendados

### Fase 6/8 — Ejecución de pruebas físicas
- Correr cada caso de prueba con procedimiento repetible.
- Registrar mediciones crudas, condiciones del ensayo y observaciones.
- Clasificar resultado: PASS / FAIL / INCONCLUSO.

**Checklist de cierre**
- [ ] Casos ejecutados con evidencia
- [ ] Resultados clasificados
- [ ] Incidencias registradas

### Fase 7/8 — Análisis de fallas e iteración
- Investigar causa raíz en FAIL/INCONCLUSO.
- Proponer correcciones (componentes, topología, layout, protección, firmware si aplica).
- Repetir pruebas impactadas y actualizar trazabilidad.

**Checklist de cierre**
- [ ] Causa raíz documentada
- [ ] Correcciones implementadas
- [ ] Revalidación completada

### Fase 8/8 — Cierre y reporte técnico
- Consolidar matriz final con cumplimiento por requisito.
- Entregar resumen ejecutivo + anexos técnicos (datos y gráficos).
- Declarar riesgos residuales y recomendaciones de siguiente versión.

**Checklist de cierre**
- [ ] Cobertura final reportada
- [ ] Cumplimiento por requisito documentado
- [ ] Riesgos residuales y acciones siguientes definidos

## Plantilla mínima de caso de prueba
- `ID:`
- `Requisito asociado:`
- `Objetivo:`
- `Condiciones iniciales:`
- `Procedimiento paso a paso:`
- `Métricas a medir:`
- `Criterio PASS/FAIL:`
- `Resultado:`
- `Evidencia:`
- `Observaciones y acciones:`

## Formato de actualización en tiempo real
En cada respuesta, usar:
1. `Fase X/Y: ...`
2. `Estado: ...`
3. `Avance: ...%`
4. `Qué se completó:`
5. `Qué sigue ahora:`
6. `Riesgos o bloqueos:`

## Configuración por defecto
- **Ámbito**: workspace.
- **Simulación prioritaria**: Proteus.
- **Criterio de salida**: no terminar sin indicar siguiente acción concreta.

## Entradas recomendadas
- Tipo de circuito/componente y versión del diseño.
- Requisitos objetivo con umbrales numéricos.
- Entorno de operación (temperatura, vibración, duty cycle, etc.).
- Instrumentos realmente disponibles.
- Restricciones de tiempo/costo.

## Salidas mínimas esperadas
- Matriz de trazabilidad completa.
- Plan y secuencia de pruebas priorizada por riesgo.
- Registro de resultados PASS/FAIL por caso.
- Hallazgos, correcciones y revalidación.
- Reporte final con riesgos residuales y próximos pasos.
