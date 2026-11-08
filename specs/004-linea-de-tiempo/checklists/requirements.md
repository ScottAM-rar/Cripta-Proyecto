# Checklist de requisitos — 004-linea-de-tiempo

Generado automáticamente el 2026-11-08 a partir de `spec.md`.

## Completitud de la especificación

- [x] La spec tiene sección de Contexto y motivación con justificación del «por qué importa».
- [x] La spec tiene al menos una Historia de usuario por prioridad P1.
- [x] Cada Historia tiene «Por qué esta prioridad» y «Prueba independiente».
- [x] Cada escenario de aceptación sigue la estructura Dado / Cuando / Entonces.
- [x] Cada escenario de aceptación cita al menos un FR.
- [x] Todos los casos del Apéndice B requeridos (casos 1–4, 6) tienen su escenario de aceptación con cita FR.
- [x] Los casos del Apéndice B 5 se referencian en «Fuera de alcance» o en contexto existente (capacidad 008).
- [x] La sección «Casos límite» cubre t=0, #1, #0, negativo, decimal, texto, partida sin acciones y retroceso con pergamino.
- [x] Todos los requisitos tienen prefijo FR-4xx empezando desde FR-427.
- [x] No hay requisitos con el mismo número FR.
- [x] Los requisitos usan DEBE / NO DEBE (lenguaje normativo).
- [x] La spec está escrita en español, desde el punto de vista del juego, sin nombrar clases ni módulos.
- [x] La spec tiene sección de Entidades clave.
- [x] La spec tiene sección de Criterios de éxito medibles (SC-xxx).
- [x] La spec tiene sección de Supuestos.
- [x] La spec tiene sección de Fuera de alcance.
- [x] Se marca correctamente que el mapa conocido (niebla de guerra) está diferido.
- [x] Se heredan y citan correctamente las decisiones de la capacidad 007.

## Consistencia con la constitución

- [x] Principio II (reproducibilidad): FR-422 de 007 referenciado; FR-429 y FR-430 son coherentes.
- [x] Principio VI (versionado de formato): se referencia FR-425 de 007 para archivos de versión anterior.
- [x] Principio VII (rendimiento medible con --bench): FR-442 y SC-006 cumplen el límite de 50 ms.
- [x] Principio VIII (spec describe reglas del juego, no implementación): cumplido; no hay clases ni módulos.
- [x] Principio IX (FR estable, Apéndice B = escenarios de aceptación): cumplido.
- [x] Principio XI (registro de prompts): pendiente de registro en PROMPTS_LLM.md.

## Ambigüedades pendientes de resolución

- [ ] **Q1** (FR-436): ¿`historia #k` con k = acciones_realizadas + 1 se acepta como estado actual o se rechaza?
- [ ] **Q2** (FR-427): ¿La consulta `historia` en una partida terminada (victoria/derrota) se acepta o se rechaza?
- [ ] **Q3** (FR-431 ítem 7): ¿Cómo se muestra (o se omite) el mapa conocido mientras la capacidad 002 no está integrada?

Una vez resueltas Q1–Q3, actualizar los FR correspondientes (FR-436, FR-427 / nota en FR-431) y marcar estos ítems como `[x]`.

## Cobertura de requisitos por historia

| Historia | FRs cubiertos |
|---|---|
| Historia 1 (historia \<t\>) | FR-427, FR-428, FR-432, FR-433, FR-434 |
| Historia 2 (historia #k) | FR-429, FR-430, FR-432, FR-434, FR-435, FR-436 |
| Historia 3 (no altera partida) | FR-432 |
| Historia 4 (pergamino) | FR-434 |
| Historia 5 (persistencia) | FR-441, Ref. FR-425 |
| Historia 6 (rendimiento) | FR-442 |
| Requisitos transversales | FR-431, FR-437, FR-438, FR-439, FR-440, FR-443 |
