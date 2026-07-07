---
name: "Brief Electrónico Pro"
description: "Recolectar y estructurar requisitos técnicos completos antes de diseñar un producto electrónico con Rex/Rex Pro."
argument-hint: "Describe el producto (qué debe hacer, entradas/salidas, alimentación, restricciones y presupuesto)."
agent: "Rex Pro"
---
Tu tarea es convertir la idea del usuario en un **brief técnico profesional y accionable** para diseño electrónico.

## Objetivo
Estandariza requisitos para que el diseño posterior (hardware + software + diagramas + Word + web) salga consistente y sin vacíos críticos.

## Instrucciones
1. Interpreta la descripción del usuario.
2. Si faltan datos críticos, formula preguntas concretas y priorizadas (máximo 12).
3. Si no hay respuesta adicional, propone supuestos razonables y márcalos explícitamente.
4. Entrega el brief final con la estructura exacta de abajo.
5. Incluye criterios de validación para seguridad, consumo, tolerancias y costo.

## Formato de salida (obligatorio)
### 1) Resumen ejecutivo
- Problema a resolver
- Función principal del sistema
- Alcance (qué sí / qué no)

### 2) Requisitos funcionales
- Entradas (sensores/señales/comandos)
- Salidas (actuadores/indicadores/comunicación)
- Reglas de operación (lógica esperada)
- Casos de uso principales

### 3) Requisitos técnicos
- Microcontrolador/plataforma preferida (si aplica)
- Tensión(es) de operación y tipo de fuente
- Corriente estimada (reposo y pico)
- Entorno de operación (temperatura, ruido, humedad, vibración)
- Restricciones físicas (tamaño, conectores, encapsulado)

### 4) Seguridad y cumplimiento
- Riesgos eléctricos relevantes
- Protecciones requeridas (fusible/PTC, flyback, aislamiento, ESD, etc.)
- Advertencias por tensión de red si aplica
- Normativa objetivo (si el usuario la menciona)

### 5) Software y control
- Lenguaje objetivo (Arduino/C/C++/Python)
- Flujo de control esperado
- Estrategia de manejo de errores
- Requisitos de telemetría/logs (si aplica)

### 6) Integración y telecomunicaciones
- Interfaces requeridas (UART/I2C/SPI/CAN/RS485/Ethernet/Wi‑Fi/Bluetooth)
- Protocolo(s) y frecuencia de intercambio
- Dependencias externas (APIs, nube, apps)

### 7) BOM preliminar y costo objetivo
- Componentes clave (lista preliminar)
- Presupuesto objetivo por unidad
- Prioridad del usuario: costo / robustez / disponibilidad

### 8) Entregables requeridos
- Hardware (BOM + conexiones)
- Software (código comentado en español)
- Diagramas renderizados (SVG/PNG)
- Documento Word estético (`.docx`)
- Página web autónoma (HTML/CSS/JS)

### 9) Criterios de aceptación
Define una checklist verificable con al menos 10 criterios medibles.

### 10) Supuestos, dudas abiertas y próximos pasos
- Supuestos adoptados
- Dudas pendientes
- Orden sugerido de implementación

## Estilo
- Responde en español técnico, claro y directo.
- Usa tablas cuando mejore legibilidad.
- Mantén consistencia en unidades y nomenclatura.
