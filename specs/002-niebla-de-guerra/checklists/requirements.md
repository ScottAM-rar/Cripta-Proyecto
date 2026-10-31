# Checklist de calidad de la especificación: Niebla de guerra y mapa conocido

**Propósito**: validar que la especificación esté completa antes de planificar
**Creada**: 2026-10-31
**Especificación**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (lenguajes, estructuras, módulos)
- [x] Enfocada en el valor para quien juega y quien revisa
- [x] Redactada para lectores no técnicos
- [x] Secciones obligatorias completas

## Completitud de requisitos

- [x] Sin marcadores [NEEDS CLARIFICATION] pendientes
- [x] Requisitos comprobables y sin ambigüedad
- [x] Criterios de éxito medibles
- [x] Criterios de éxito sin detalles de tecnología
- [x] Escenarios de aceptación definidos
- [x] Casos límite identificados
- [x] Alcance acotado
- [x] Dependencias y supuestos identificados

## Preparación

- [x] Todo requisito funcional se cubre con algún escenario (FR-201 a FR-226, todos citados)
- [x] Los escenarios cubren los flujos principales (incluye los 3 casos del Apéndice B)
- [x] Cumple los resultados medibles
- [x] No se filtran detalles de implementación

## Notas

- Las 2 dudas iniciales (FR-209 y FR-221) se resolvieron en la sesión de clarificación 2026-10-31 (ver spec.md).
- Los requisitos de rendimiento (FR-223 a FR-226) se expresan como crecimiento respecto del tamaño, sin nombrar estructuras.
- 2026-10-31 (implement T001): plan y tareas revisados contra la lista de prohibidos del principio I; sin hallazgos. Se recorre el `deque` de `SalaDTO.salidas` solo en lectura; no se agrega ningún uso nuevo de `deque`, `dict`, `set`, `sorted()` ni `list.sort()`.
