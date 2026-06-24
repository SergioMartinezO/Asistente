---
name: "Revisión Final de Entrega"
description: "Auditar paquete final de diseño electrónico (hardware, software, diagramas, Word y web) con checklist de calidad antes de entregar al cliente."
argument-hint: "Pega el resumen final del proyecto y/o lista de archivos generados para auditar la entrega."
agent: "Rex Pro"
---
Tu tarea es realizar una **revisión final integral** del paquete de entrega de un producto electrónico.

## Objetivo
Detectar omisiones, inconsistencias y riesgos de calidad antes de la entrega al usuario final o cliente.

## Alcance de revisión
Evalúa estos cinco entregables:
1. Hardware
2. Software
3. Diagramas renderizados (SVG/PNG)
4. Documento Word (`.docx`)
5. Página web (`index.html`)

## Instrucciones
1. Revisa cada entregable contra los requisitos del brief original.
2. Identifica inconsistencias cruzadas (ejemplo: pines en hardware que no coinciden con software).
3. Evalúa calidad técnica, legibilidad documental y claridad de presentación.
4. Clasifica hallazgos por severidad: **Crítico / Mayor / Menor / Mejora**.
5. Entrega una lista de correcciones priorizadas.
6. Si falta evidencia para aprobar un punto, márcalo como "No verificable".

## Checklist obligatorio de auditoría
### A) Hardware
- BOM completa con valores, referencias y función técnica.
- Coherencia de tensiones y GND común.
- Protecciones eléctricas adecuadas (fusible/PTC/flyback/aislamiento cuando aplique).
- Fuente con margen suficiente.

### B) Software
- Código completo, ejecutable y comentado en español.
- Coherencia de nombres de pines/variables con el esquema.
- Manejo de errores y estados no válidos.
- Lógica de control explicada y verificable.

### C) Diagramas
- Existe al menos un diagrama de circuito y uno funcional.
- Legibilidad (texto, símbolos, conexiones, flujo).
- Coherencia con BOM y software.

### D) Documento Word
- Portada con título y autor.
- Secciones técnicas bien estructuradas.
- Tabla de componentes correcta.
- Diagramas insertados correctamente.
- Redacción profesional sin contradicciones.

### E) Página web
- Abre sin dependencias externas obligatorias.
- Diagrama embebido visible.
- Explicación funcional breve y correcta.
- Consistencia con Word y diseño técnico.

### F) Validación Pro
- Seguridad eléctrica: riesgos y mitigaciones explícitas.
- Consumo estimado (reposo/pico) y margen de fuente.
- Tolerancias/derating documentados.
- Costo estimado y alternativas de componentes.

## Formato de salida (obligatorio)
### 1) Estado general
- **Aprobación final**: Aprobado / Aprobado con cambios / Rechazado
- Resumen ejecutivo (3–6 líneas)

### 2) Matriz de hallazgos
Tabla con columnas:
- ID
- Categoría (Hardware/Software/Diagrama/Word/Web/Validación Pro)
- Severidad
- Hallazgo
- Evidencia
- Acción correctiva recomendada

### 3) Checklist de cumplimiento
- Lista con cada ítem del checklist marcado como:
  - Cumple
  - No cumple
  - No verificable

### 4) Plan de cierre
- Top 5 correcciones prioritarias en orden de impacto.
- Riesgo residual si se entrega sin corregir.
- Recomendación de entrega final.

## Estilo
- Español técnico, concreto y accionable.
- No describas teoría innecesaria.
- Prioriza claridad para ejecutar correcciones rápidamente.
