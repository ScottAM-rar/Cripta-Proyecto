# Registro de comandos `/speckit` con texto propio

Constitución, principio XI: todo comando `/speckit` con texto propio se registra con herramienta y modelo. Esto complementa a `bitacora-prompts-equipo.md` (prompts libres por integrante).

> **Nota**: las entradas resumen el texto que se dio a cada comando. Si el grupo necesita el texto literal, debe copiarlo del historial de la sesión. Quien confirme estas entradas debe poder explicar y defender cada especificación y cada decisión (principio XI).

Herramienta en todas las entradas: Spec Kit 1.2.3 con Claude Code. Modelo: `claude-sonnet-5-5`. Fecha: 2026-10-27. Sesión de: Cesar Segura Galeano.

| # | Comando | Texto propio (resumen) | Resultado |
|---|---|---|---|
| 1 | `/speckit-constitution` | Constitución de CRIPTA en español y tono normativo: contexto (Parte I vigente, cuatro capacidades de la Parte II), once principios (estructuras propias, determinismo, equivalencia ante el reuso, MVC y adaptadores, sin datos de una cripta, presupuesto de red y versiones, rendimiento medido, especificación primero, trazabilidad, cambios de especificación, uso de LLM), flujo obligatorio y gobernanza | `.specify/memory/constitution.md` v1.0.0 |
| 2 | `/speckit-specify` | Capacidad terreno y cazador: costo de las salidas (por defecto 100, igual en ambos sentidos), comportamiento cazador con rango, reglas de decisión y desempate por menor id, conocimiento del esqueleto completo, equivalencia con calcular desde cero, datos, interfaz, rendimiento y escenarios de aceptación | `specs/001-terreno-y-cazador/spec.md` |
| 3 | `/speckit-clarify` (respuestas: A, B, A) | Puerta que se cierra durante un cruce: se completa. Costo de salida inválido: 100 con advertencia. Rango ausente o inválido: 0 con advertencia | Sección Clarificaciones de `spec.md`; FR-101, FR-108, FR-109 |
| 4 | `/speckit-plan` (sin texto adicional) | — | `plan.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md` |
| 5 | `/speckit-tasks` (sin texto adicional) | — | `tasks.md` |
| 6 | `/speckit-implement` (sin texto adicional) y respuestas durante la ejecución | Costos distintos en los dos lados: gana la sala de menor id; conexiones de un solo sentido: válidas; control de versiones: no confirmar nada | Código, pruebas y `mediciones.md`; FR-102 ampliado y FR-124 nuevo en `spec.md` |
