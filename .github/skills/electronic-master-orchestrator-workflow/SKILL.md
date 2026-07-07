---
name: electronic-master-orchestrator-workflow
description: 'Orquesta un flujo maestro 1-click para proyectos electrónicos: diseño del componente, plan de pruebas y reporte final, con compuertas de calidad, continuidad de explicación y avance en tiempo real.'
argument-hint: 'Proyecto, tipo de componente, objetivos eléctricos, restricciones, entorno de pruebas y formato final requerido.'
user-invocable: true
disable-model-invocation: false
---

# Workflow Maestro Electrónico (diseño → pruebas → reporte)

## Cuándo usar
- Cuando se requiere ejecutar un proyecto electrónico de punta a punta con una sola invocación.
- Cuando se necesita trazabilidad completa entre diseño, validación y cierre documental.
- Cuando el usuario exige explicación continua (sin cortes) y estado en tiempo real.

## Skills dependientes
Este flujo maestro se integra y delega en:
- `electronic-component-design-workflow`
- `electronic-test-plan-workflow`
- `electronic-final-report-workflow`

## Resultado esperado
- Diseño técnico estructurado con decisiones justificadas.
- Plan de pruebas ejecutable con criterios PASS/FAIL y evidencia.
- Informe final con conclusiones, riesgos residuales y próximos pasos.

## Reglas de operación obligatorias
1. No interrumpir la explicación: siempre cerrar cada respuesta con siguiente acción concreta.
2. Mostrar progreso en tiempo real en cada fase:
   - `Fase X/4: <nombre>`
   - `Estado: en curso | completada | bloqueada`
   - `Avance: <0-100>%`
   - `Siguiente acción: <acción concreta>`
3. No avanzar de fase sin pasar compuerta de calidad de la fase actual.
4. Si faltan datos, declarar supuestos explícitos, evaluar impacto y continuar.

## Procedimiento maestro

### Fase 1/4 — Kickoff y normalización de entradas
- Recopilar: objetivo, tipo de componente, Vin/Vout, corriente, frecuencia, precisión, restricciones (costo/tamaño/temperatura), normas y plazo.
- Normalizar requerimientos en formato único para reutilizarlos en todas las fases.
- Definir criterio global de éxito del proyecto.

**Compuerta de calidad G1 (obligatoria)**
- [ ] Requisitos críticos completos
- [ ] Restricciones documentadas
- [ ] Criterio de éxito global definido

### Fase 2/4 — Diseño del componente (delegar a skill de diseño)
- Ejecutar flujo completo de `electronic-component-design-workflow`.
- Capturar como entregables mínimos:
  - arquitectura de bloques,
  - BOM preliminar,
  - esquemático/cálculos clave,
  - resultados de simulación inicial.

**Compuerta de calidad G2 (obligatoria)**
- [ ] Diseño coherente con requisitos
- [ ] Simulación inicial alineada al objetivo
- [ ] Riesgos técnicos preliminares identificados

### Fase 3/4 — Validación y pruebas (delegar a skill de pruebas)
- Ejecutar flujo de `electronic-test-plan-workflow`.
- Construir matriz de trazabilidad requisito→prueba→resultado.
- Clasificar resultados: PASS / FAIL / INCONCLUSO.

**Compuerta de calidad G3 (obligatoria)**
- [ ] Cobertura de requisitos validada
- [ ] Evidencia de pruebas consolidada
- [ ] Fallas críticas resueltas o acotadas

### Fase 4/4 — Informe técnico final (delegar a skill de reporte)
- Ejecutar `electronic-final-report-workflow`.
- Consolidar conclusión por requisito y conclusión global.
- Generar plan de acción para riesgos residuales.

**Compuerta de calidad G4 (obligatoria)**
- [ ] Informe final consistente y trazable
- [ ] Riesgos residuales con mitigación
- [ ] Recomendación clara de siguiente etapa

## Política de rollback (si falla una compuerta)
- Si falla G2: regresar a diseño (ajustar arquitectura/BOM/simulación).
- Si falla G3: regresar a pruebas (replantear casos, instrumentación o correcciones técnicas).
- Si falla G4: regresar a consolidación de resultados y evidencias.

## Formato de salida por iteración
En cada actualización, incluir:
1. `Fase X/4: ...`
2. `Estado: ...`
3. `Avance: ...%`
4. `Entregables generados:`
5. `Compuerta actual (G1/G2/G3/G4): APROBADA | RECHAZADA`
6. `Qué sigue ahora:`
7. `Riesgos/supuestos:`

## Entradas recomendadas
- Nombre del proyecto y versión objetivo.
- Tipo de componente y parámetros eléctricos clave.
- Restricciones (costo, tamaño, ambiente, normativa).
- Herramienta de simulación preferida (default: Proteus).
- Nivel de detalle esperado del informe final (ejecutivo/técnico/mixto).

## Salidas mínimas esperadas
- Paquete de diseño (arquitectura + BOM + simulación).
- Paquete de validación (plan + matriz + resultados).
- Paquete de cierre (informe final + riesgos + plan de acción).

## Prompt de activación recomendado
`Ejecuta el workflow maestro electrónico completo de punta a punta para [proyecto], sin cortar explicación y mostrando avance en tiempo real.`
