# Checklist de calidad de la especificación: Recorrido por niveles

**Propósito**: validar que la especificación esté completa antes de planificar
**Creada**: 2026-10-27
**Especificación**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (lenguajes, estructuras, módulos)
- [x] Enfocada en el valor para quien revisa y para las funciones que lo usan
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

- [x] Todo requisito funcional se cubre con algún escenario
- [x] Los escenarios cubren los flujos principales
- [x] Cumple los resultados medibles
- [x] No se filtran detalles de implementación

## Notas

- Resueltos en la sesión de clarificación 2026-10-27: desempate por menor id (FR-502) y salidas transitables declaradas por quien pide el recorrido (FR-507).
- El escenario 8 del enunciado (dos ejecuciones iguales) quedó como Historia 3, escenario 1 (FR-509).
- Se agregó FR-512 (origen inexistente), no pedido en el enunciado, por ser un caso límite que el enunciado no cubre; revisar si el grupo lo quiere.
- FR-510 no se mide con un número fijo de milisegundos porque el enunciado pide proporcionalidad; SC-004 la concreta como a lo sumo el doble al multiplicar el tamaño de la cripta por 100.
