# Documento de Decisiones (Parte II)

Por capacidad: enlace a su especificación y a su plan, si la decisión final coincide con el plan original y, si no, qué medición motivó el cambio (constitución, flujo obligatorio). Las decisiones de la Parte I siguen en `DOCUMENTACION_DECISIONES_DISENO.md`.

## 001 · Terreno y cazador

- Especificación: [`specs/001-terreno-y-cazador/spec.md`](specs/001-terreno-y-cazador/spec.md) (FR-101 a FR-131)
- Plan: [`specs/001-terreno-y-cazador/plan.md`](specs/001-terreno-y-cazador/plan.md), con [`research.md`](specs/001-terreno-y-cazador/research.md)
- Mediciones: [`specs/001-terreno-y-cazador/mediciones.md`](specs/001-terreno-y-cazador/mediciones.md)

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| Mapa del esqueleto en listas contiguas, aristas salientes y entrantes; estado de puertas leído de la sala cargada o, si no está cargada, el inicial | Sí | `test_cazador` (FR-117) y `test_determinismo_cazador`: misma decisión con y sin salas descargadas |
| Búsqueda de menor costo desde la sala del jugador, acotada por el rango, con montículo propio y reinicio por marca de época | Sí | `--bench terreno` B: 28 µs frente a 57 ms sin cota a 40 000 salas |
| Campo compartido por todos los cazadores del instante | Sí | `--bench terreno` A: con 50 cazadores, 17 µs (jugador quieto) y 77 µs (jugador moviéndose) frente a ≈ 3 ms calculando por cazador |
| Invalidación por evento, con un punto único de cambio de puertas (`PuertasLogica.fijar_cerrada`) | Sí | `--bench terreno` C: 0 búsquedas frente a 18 por 40 ciclos con puertas lejanas; `test_equivalencia_cazador` y `test_puertas_punto_unico` |
| El contrato de los comportamientos devuelve `AccionEnemigoDTO` (mensaje y costo) | Sí | El siguiente evento del actor se programa con el costo de la salida cruzada (FR-103) |
| Costo inválido → 100 con advertencia; rango ausente o inválido → 0 con advertencia | Sí (decidido en `/speckit-clarify`) | Clarificaciones 2 y 3 de `spec.md` |
| Costos distintos en los dos lados → gana la sala de menor id; conexiones de un solo sentido válidas | **Cambió respecto del plan original**: el plan dejaba ambos puntos como «regla provisional» | Se resolvieron en la especificación antes de implementar (FR-102 ampliado, FR-124 nuevo) |
| Ids de sala densos desde 1 (no desde 0) | **Corrección al plan**: `research.md` decía 0..N−1 | El código de la Parte I usa listas de tamaño N+1 indexadas por id; las estructuras se dimensionan con el mayor id más uno |
| Formato de partida: `VERSION_ESTADO` 3 y `VERSION_FORMATO` 6; los archivos anteriores se rechazan | Sí | `test_terreno_costos` (FR-119) |
| Mediciones de la Parte I repetidas con la carga nueva | Sí: ninguna decisión de la Parte I dejó de servir | `mediciones.md`: binario sigue ≈ 2,9× menor que JSON y ≈ 128× más rápido para una sala; +3 % de tamaño por el costo de cada salida |
| Búsqueda de rutas generalizada (`BuscadorRutas`) sobre una vista del mapa, para que otras capacidades la reutilicen con el mapa conocido | **Cambió respecto del plan original**: el plan tenía la búsqueda dentro del campo de costos | Ampliación del plan (2026-10-29): 197 pruebas en OK, decisiones idénticas a calcular desde cero (12 000 comparaciones, 0 diferencias) y ciclo dentro de 20 ms. Alternativa descartada (campo sin vista, T071): la vista cuesta entre 14 % y 22 % más (50 cazadores con el jugador quieto: 33,0 µs frente a 40,2 µs; 200 cazadores con el jugador moviéndose: 193 µs frente a 226 µs) y el peor ciclo sigue en ≈ 0,25 ms frente al límite de 20 ms. Se mantiene la vista porque permite buscar sobre el mapa conocido. `mediciones.md`, sección «Búsqueda con vista» |
| `MapaCripta` con `total_salas`, `salidas(sala)`, `entrantes(sala)` y `version_puertas`; la versión la sube solo `fijar_cerrada` | **Cambió respecto del plan original**: se agregó como contrato compartido | `test_mapa_cripta.py` y `test_puertas_punto_unico.py`. Al restaurar una partida se crea un `MapaCripta` nuevo, así que `version_puertas` empieza de cero con el estado restaurado y no hace falta subirla |

## 005 · Recorrido por niveles

- Especificación: [`specs/005-recorrido-por-niveles/spec.md`](specs/005-recorrido-por-niveles/spec.md) (FR-501 a FR-513)
- Plan: [`specs/005-recorrido-por-niveles/plan.md`](specs/005-recorrido-por-niveles/plan.md), con [`research.md`](specs/005-recorrido-por-niveles/research.md)
- Mediciones: [`specs/005-recorrido-por-niveles/mediciones.md`](specs/005-recorrido-por-niveles/mediciones.md)

| Decisión | ¿Coincide con el plan original? | Medición o motivo |
|---|---|---|
| Visitados con marca de época, dos listas indexadas por id de sala | Sí | SC-004 por conteo: un recorrido de 2 niveles visita 13 salas y examina 20 salidas en 400, 4 900 y 40 000 salas (`test_recorrido_proporcional` y `--bench recorrido`, sección A) |
| Cola circular propia sobre una lista | Sí (instrucción del grupo), **con una observación abierta** | Frente a `pop(0)` gana en frontera ancha (árbol: 25,1 ms frente a 41,1 ms). Pero las **dos listas por nivel** (sin cola) son 8 % a 14 % más rápidas en las tres criptas medidas, como anticipaba `research.md` §3. No se cambió: la diferencia es pequeña y la cola fue pedida. **Decisión pendiente del grupo** |
| Ordenar cada nivel con `ordenar_adaptativo` (no `sorted()`) | Sí | El orden de descubrimiento sigue al de los padres, no al de los ids (ejemplo `1, 3, 5, 4, 9`). Frente al montículo `(nivel, id)`: el montículo es 19 % (rejilla) y 46 % (árbol) más lento |
| `MapaCripta.existe` para rechazar un origen inexistente y ignorar salidas hacia salas inexistentes | Sí | `test_recorrido_por_niveles` (FR-512, FR-513) |
| El criterio de transitabilidad lo pasa quien pide el recorrido; sin criterio valen todas | Sí | Clarificación 2026-10-27; `TestOrdenYAlcance` |
| SC-004 se verifica por conteo y la razón de tiempos solo informa | **Cambió respecto de la especificación original**, que usaba una razón de tiempos (≤ 2×) | `/speckit-analyze` (A1): el tiempo de operaciones de decenas de µs es frágil. Medido: la razón fue 0,99× |
| FR-513: una salida hacia una sala que no existe se ignora | **Agregado a la especificación tras `/speckit-analyze` (S1)**; el plan ya lo suponía | `TestOrigenYSalasInexistentes` y la equivalencia con la referencia |
| `ServicioCripta.salas_vecinas` no se modifica | Sí | Medido como referencia: con límite 5 en 40 000 salas tarda 11,75 ms frente a 0,02 ms del recorrido nuevo, porque busca cada sala con un recorrido lineal. Reemplazarlo le toca a la capacidad que adopte el recorrido |
