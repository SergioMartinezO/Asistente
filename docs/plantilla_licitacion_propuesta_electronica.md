# Plantilla operativa — Licitación / Propuesta comercial técnica (dispositivo electrónico)

Usa esta plantilla para exigir una propuesta profesional con estructura de pre-venta, diseño técnico y condiciones de implementación.

Plantillas relacionadas:

- Índice maestro: [`plantillas_indice.md`](./plantillas_indice.md)
- Diseño técnico base: [`plantilla_prompt_diseno_electronico.md`](./plantilla_prompt_diseno_electronico.md)
- Costos/riesgos/KPIs: [`plantilla_prompt_diseno_electronico_costos_riesgos.md`](./plantilla_prompt_diseno_electronico_costos_riesgos.md)

---

## 1) Plantilla lista para copiar y pegar

Actúa como consultor senior en ingeniería electrónica y prepara una **propuesta comercial técnica completa** para el siguiente proyecto.

### Datos base

- **Proyecto**: [NOMBRE DEL PROYECTO]
- **Cliente**: [EMPRESA / ENTIDAD]
- **Sector**: [INDUSTRIA / SALUD / AGRO / EDUCACIÓN / OTRO]
- **Objetivo de negocio**: [RESULTADO ESPERADO]
- **Objetivo técnico**: [QUÉ DEBE HACER EL SISTEMA]
- **Fecha de inicio objetivo**: [YYYY-MM-DD]
- **Duración objetivo**: [N semanas/meses]

### Requisitos de la propuesta

1. **Resumen ejecutivo** (1 página): problema, solución, beneficios esperados.
2. **Alcance del proyecto**:
   - En alcance (in scope),
   - Fuera de alcance (out of scope),
   - Supuestos y dependencias.
3. **Arquitectura técnica**:
   - Hardware,
   - Software,
   - Comunicaciones,
   - Seguridad.
4. **Plan de implementación por fases** con inicio/fin por fase y entregables.
5. **Cronograma consolidado** con hitos críticos y ruta crítica resumida.
6. **Presupuesto detallado**:
   - CAPEX,
   - OPEX,
   - contingencia,
   - total estimado.
7. **Modelo de riesgos**:
   - riesgo,
   - probabilidad,
   - impacto,
   - mitigación,
   - responsable.
8. **Criterios de aceptación** por entregable.
9. **Plan de pruebas y aseguramiento de calidad** (funcionales, integración, estrés, seguridad).
10. **SLA y soporte post-implementación**:
    - tiempos de respuesta,
    - tiempos de resolución,
    - ventana de soporte,
    - escalamiento.
11. **Garantías técnicas y condiciones comerciales**:
    - garantía de hardware,
    - garantía de software,
    - exclusiones,
    - forma de pago,
    - validez de la oferta.
12. **KPIs de éxito** a 3, 6 y 12 meses.
13. **Conclusión de viabilidad**:
    - técnica,
    - económica,
    - operativa.

### Formato obligatorio de salida

- Secciones numeradas y lenguaje profesional.
- Tablas para cronograma, costos, riesgos, SLA y KPIs.
- Fechas en formato `YYYY-MM-DD`.
- Cierre con: **"Propuesta lista para aprobación y ejecución"**.

---

## 2) Parámetros opcionales para mayor precisión

- **budget_ceiling_usd**: [tope máximo de inversión]
- **target_go_live_date**: [YYYY-MM-DD]
- **required_certifications**: [CE/FCC/RETIE/IEC/ISO]
- **availability_target**: [ej. 99.9%]
- **max_downtime_per_month**: [horas]
- **support_model**: [8x5 / 24x7 / híbrido]
- **penalty_clause_required**: [sí/no]

---

## 3) Mini-checklist de revisión interna

- [ ] El alcance y exclusiones están claros.
- [ ] El cronograma por fases tiene fechas realistas.
- [ ] El presupuesto tiene CAPEX/OPEX y contingencia.
- [ ] Los riesgos tienen mitigación y responsable.
- [ ] El SLA y soporte están detallados.
- [ ] La propuesta cierra con viabilidad completa.

---

## 4) Ejemplo corto de uso

Genera una propuesta comercial técnica para implementar un sistema de monitoreo energético industrial con nodos IoT, tablero web y alertas predictivas.

Inicio objetivo: 2026-08-01
Duración objetivo: 14 semanas
Disponibilidad mínima: 99.8%
Soporte requerido: 24x7
Tope CAPEX: 45,000 USD

Entrega alcance, cronograma por fases con entregables, presupuesto detallado, riesgos, SLA, garantías y conclusión de viabilidad técnica/económica/operativa.
