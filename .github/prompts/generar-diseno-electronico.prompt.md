---
name: "Generar Diseño Electrónico Completo"
description: "Tomar un brief técnico y generar el paquete final de diseño: hardware, software, diagramas SVG/PNG, documento Word (.docx) y web HTML/CSS/JS."
argument-hint: "Pega aquí el brief técnico completo o la especificación final del producto."
agent: "Rex Pro"
---
A partir del brief proporcionado por el usuario, genera un **paquete técnico final completo** y listo para implementación.

## Objetivo
Convertir requisitos en una solución integral con artefactos técnicos y de presentación, manteniendo trazabilidad entre requerimientos, hardware y software.

## Instrucciones de ejecución
1. Analiza el brief y detecta vacíos críticos.
2. Si falta información indispensable, plantea preguntas mínimas (máximo 8); si no hay respuesta, usa supuestos explícitos.
3. Diseña el hardware con BOM, conexiones, protecciones y justificación técnica.
4. Genera software completo (Arduino/C/C++/Python según el caso), comentado en español.
5. Crea y renderiza diagramas claros (circuito + bloques funcionales) en SVG/PNG.
6. Genera documento Word profesional (`.docx`) con portada, autor, secciones, tablas y diagramas insertados.
7. Construye página web autónoma (HTML/CSS/JS) con explicación funcional y diagrama embebido.
8. Ejecuta validación Pro: seguridad eléctrica, consumo, tolerancias/derating y costo estimado.
9. Verifica consistencia final entre todos los entregables.

## Formato de salida (obligatorio)
### 1) Hardware
- BOM detallada (tabla)
- Conexiones pin a pin
- Justificación técnica de componentes
- Protecciones implementadas

### 2) Software
- Código completo
- Explicación de la lógica paso a paso
- Estrategia de manejo de errores

### 3) Diagramas renderizados
- Lista de archivos generados (SVG/PNG)
- Breve interpretación técnica de cada diagrama

### 4) Documento Word
- Ruta del `.docx`
- Contenido incluido (portada, BOM, secciones, diagramas, resultados)

### 5) Página web
- Ruta de `index.html`
- Estructura de la página (secciones y recursos embebidos)

### 6) Validación Pro
- Seguridad eléctrica (riesgos y mitigaciones)
- Consumo estimado (reposo/pico) y margen de fuente
- Tolerancias y derating aplicados
- Costo unitario estimado y alternativas

### 7) Supuestos, límites y mejoras
- Supuestos adoptados
- Límites del diseño
- Próximas mejoras sugeridas

## Criterios de calidad
- Claridad y viabilidad de implementación real.
- Coherencia entre especificación, hardware y software.
- Diagramas legibles y reutilizables en documentación.
- Documento Word profesional y web presentable sin dependencias externas obligatorias.

## Nota de estilo
Responde en español técnico, directo y ordenado. Prioriza tablas para BOM y validaciones cuando mejore la lectura.
