---
name: electronic-component-design-workflow
description: 'Guía completa para iniciar y ejecutar diseño de componente electrónico. Usar cuando el asistente deba explicar sin cortes: requisitos, selección de materiales, diseño de circuito, simulación, pruebas e iteración, mostrando progreso en tiempo real.'
argument-hint: 'Tipo de componente, aplicación, restricciones (costo/tamaño/temperatura), normas, y plazo objetivo.'
user-invocable: true
disable-model-invocation: false
---

# Flujo de Diseño de Componente Electrónico (sin cortes)

## Cuándo usar
- Al iniciar un nuevo proyecto de diseño de componente electrónico.
- Cuando se requiere una explicación continua, clara y accionable de principio a fin.
- Cuando el usuario necesita ver el avance en tiempo real durante el proceso.

## Resultado esperado
- Un plan técnico completo para diseñar, simular, prototipar y probar el componente.
- Decisiones justificadas de materiales y topología de circuito.
- Evidencias de verificación (simulación + pruebas) y criterios de aceptación.

## Reglas de comunicación obligatorias
1. **No interrumpir la explicación**: nunca terminar de forma abrupta; siempre cerrar con siguiente paso inmediato.
2. **Progreso en tiempo real**: mostrar estado por fases con formato fijo:
   - `Fase X/Y: <nombre>`
   - `Estado: en curso | completada | bloqueada`
   - `Avance: <0-100>%`
   - `Siguiente acción: <acción concreta>`
3. **Desglose accionable**: cada fase termina con mini-checklist de verificación.
4. **Gestión de bloqueo**: si falta información crítica, continuar con supuestos explícitos y marcar riesgo.

## Procedimiento

### Fase 1/7 — Definición del problema y requisitos
- Objetivo funcional del componente.
- Variables de entrada/salida, niveles eléctricos y potencia.
- Restricciones: costo, tamaño, temperatura, disponibilidad de partes, normativas.
- Entorno de uso: industrial, consumo, automotriz, médico, etc.

**Checklist de cierre**
- [ ] Requisitos eléctricos definidos
- [ ] Restricciones no funcionales definidas
- [ ] Criterios de éxito definidos

### Fase 2/7 — Arquitectura y selección de enfoque
- Elegir arquitectura: analógica, digital o mixta.
- Definir bloques funcionales (alimentación, acondicionamiento, control, protección, salida).
- Seleccionar topología preliminar del circuito por bloque.

**Decisiones clave (branching)**
- Si el consumo es alto: priorizar eficiencia, térmica y protección.
- Si la señal es sensible: priorizar ruido, filtrado y layout.
- Si el costo manda: priorizar BOM mínima y componentes de alta disponibilidad.

**Checklist de cierre**
- [ ] Bloques funcionales aprobados
- [ ] Topología preliminar definida

### Fase 3/7 — Selección de materiales y componentes
- Seleccionar componentes por bloque (ICs, pasivos, conectores, disipación, PCB).
- Evaluar criterios: parámetros eléctricos, tolerancia, temperatura, encapsulado, lifecycle, lead time.
- Definir alternativas A/B para cada componente crítico.

**Criterios mínimos**
- Derating de voltaje/corriente.
- Tolerancias compatibles con el desempeño objetivo.
- Disponibilidad en distribuidores confiables.

**Checklist de cierre**
- [ ] BOM preliminar creada
- [ ] Sustitutos definidos para componentes críticos
- [ ] Riesgos de suministro evaluados

### Fase 4/7 — Diseño de circuito
- Elaborar esquema completo con protecciones (sobrecorriente, inversión de polaridad, ESD cuando aplique).
- Cálculo de valores (resistencias, capacitores, realimentación, filtros, estabilidad).
- Definir puntos de test y medición desde el inicio.

**Checklist de cierre**
- [ ] Esquemático completo
- [ ] Cálculos documentados
- [ ] Puntos de prueba definidos

### Fase 5/7 — Simulación
- Configurar simulaciones DC, AC, transitorio y peores casos (tolerancia/temperatura) según aplique.
- Validar estabilidad, respuesta dinámica, eficiencia y márgenes.
- Registrar resultados y discrepancias frente a objetivos.

**Checklist de cierre**
- [ ] Casos nominal y extremos simulados
- [ ] Resultados comparados contra requisitos
- [ ] Ajustes propuestos documentados

### Fase 6/7 — Prototipo y pruebas
- Preparar plan de pruebas: funcional, estrés térmico, variación de carga/frecuencia, seguridad.
- Definir instrumentos, procedimiento, criterios de aceptación y formato de registro.
- Ejecutar pruebas y capturar evidencia (tablas, gráficas, observaciones).

**Checklist de cierre**
- [ ] Plan de pruebas aprobado
- [ ] Evidencias capturadas
- [ ] No conformidades registradas

### Fase 7/7 — Iteración y cierre técnico
- Corregir hallazgos (circuito, componentes o layout).
- Validar versión final contra criterios de aceptación.
- Entregar paquete final: esquema, BOM final, resultados de simulación, reporte de pruebas y riesgos residuales.

**Checklist de cierre**
- [ ] Requisitos cumplidos
- [ ] Riesgos residuales documentados
- [ ] Entregables finales listos

## Formato de respuesta recomendado para el asistente
Usar este patrón en cada actualización:
1. `Fase X/Y: ...`
2. `Avance: ...%`
3. `Qué se completó:` (bullets cortos)
4. `Qué sigue ahora:` (1-3 acciones concretas)
5. `Riesgos o supuestos:` (si aplica)

## Política de continuidad (anti-corte)
- No finalizar una respuesta sin incluir: **estado + siguiente acción + criterio de cierre de la fase actual**.
- Si la respuesta se vuelve extensa, dividir en “Parte 1/2”, “Parte 2/2” sin perder continuidad.
- Si hay incertidumbre, declarar supuestos y continuar con el plan.

## Entradas recomendadas
- Tipo de componente (ej. regulador, sensor, driver, filtro, etapa de potencia).
- Especificaciones objetivo (Vin/Vout, corriente, frecuencia, precisión, eficiencia).
- Restricciones (costo, tamaño, ambiente, normativa).
- Herramienta de simulación disponible (**prioridad por defecto: Proteus**).

## Configuración por defecto para este skill
- **Ámbito**: workspace (proyecto compartido).
- **Simulación prioritaria**: Proteus.
- **Formato de progreso en tiempo real**: porcentaje + fase + siguiente acción.

## Salidas mínimas esperadas
- Requisitos estructurados.
- Arquitectura y justificación.
- BOM preliminar/final.
- Esquemático con cálculos clave.
- Resultados de simulación y plan de pruebas.
- Estado de avance y próximos pasos en tiempo real.
