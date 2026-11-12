# Lista de calidad de la especificación: Comando «ir a»

**Propósito**: validar completitud y calidad antes de planificar
**Creada**: 2026-11-11
**Especificación**: [spec.md](../spec.md)

## Calidad del contenido

- [x] Sin detalles de implementación (módulos, clases, estructuras)
- [x] Centrada en el valor para quien juega y quien revisa
- [x] Comprensible sin conocer el código
- [x] Todas las secciones obligatorias completas

## Completitud de requisitos

- [x] Sin marcadores [NEEDS CLARIFICATION]
- [x] Requisitos comprobables y sin ambigüedad
- [x] Criterios de éxito medibles
- [x] Criterios de éxito sin detalles de implementación
- [x] Escenarios de aceptación definidos (B-N1, B-N2, B-N3, B-N6 trazados)
- [x] Casos límite identificados
- [x] Alcance acotado (fuera de alcance explícito)
- [x] Dependencias y supuestos identificados (002, 001, Parte I §2.4)

## Preparación de la funcionalidad

- [x] Todos los requisitos tienen criterio de aceptación
- [x] Las historias cubren los flujos principales
- [x] Cumple los resultados medibles
- [x] Sin fugas de implementación

## Notas

- FR-249 queda fuera de orden numérico (se agregó al ordenar por tema); es estable.
- El nombre del módulo de rutas del encargo no se cita en la spec (constitución VIII); va en `plan.md`.
- T001 (2026-11-11): revisión de plan.md y tasks.md contra el principio I. La ruta usa BuscadorRutas (MonticuloMinimo propio) y listas indexadas por id; el resultado del viaje lleva una lista `recorrido`; ningún dict, set, heapq, bisect, collections, networkx, sorted() ni list.sort() en el diseño. Las referencias de prueba usan listas.
- T027 (2026-11-11): la historia 5 (antorcha) se cumple por construcción del paso: la antorcha actúa dentro de `MapaConocido.entrar`, llamado por el gestor durante el movimiento. `test_viaje_antorcha.py` pasa sin cambios en `ViajeLogica`.
- T034 (2026-11-11): no hace falta llamar a `ingresarEnSala` antes de comprobar `FIN_IR_A` (hallazgo C2): los dormidos se activan dentro del movimiento. La repetición verifica la sala final y vuelve a escribir las marcas.
- Hallazgo en la 002 (no corregido aquí): `MapaConocido._posicion_adyacente` recorre todas las salidas de la sala origen de una arista entrante y compara por identidad; por eso cerrar la puerta este de la sala 2 con el jugador en la sala 1 (vecina) la marca cerrada en el mapa aunque no conecta la sala 1 (FR-207 pide observar solo en las dos salas que conecta). Las pruebas de B-N2 de 006 usan una puerta a dos salas del jugador.
- T044 (2026-11-11): búsqueda de usos prohibidos en `Logica/ViajeLogica.py`, `DTO/ResultadoViajeDTO.py`, `bench/ir_a.py`, las pruebas `test_viaje_*.py`, `tests_labs/escenarios_ir_a.py`, `tests_labs/referencia_viaje.py` y los cambios de `Logica/EstadoJuegoLogica.py` y `Logica/LogEventos.py`: sin `dict`, `set`, `heapq`, `bisect`, `collections`, `networkx`, `sorted()` ni `.sort()` (la prueba de enemigos usa `insertion_sort`); el modelo no importa red, disco ni vista; sin literales de la cripta de desarrollo (todo sale de criptas sintéticas). Las coincidencias de la búsqueda son solo palabras en docstrings.

## Trazabilidad requisito → escenario → prueba

| Requisito | Escenario (historia) | Prueba |
|---|---|---|
| FR-231 | H1 esc. 1, 3; caso límite de la antorcha | `test_viaje_ruta` (`test_FR231_*`), `test_viaje_comando` |
| FR-232, FR-233 | H1 esc. 1 | `test_viaje_ruta::test_FR231_FR232_FR233_*`, `test_FR232_*`; `test_viaje_equivalencia::test_FR233_FR236_*` |
| FR-234 | H1 esc. 2 | `test_viaje_ruta::test_FR234_*` (diamante y rejillas con empates); `--bench ir_a` A |
| FR-235 | H1 esc. 4 | `test_viaje_ruta::test_FR235_*` |
| FR-236 | H1 esc. 5 | `test_viaje_equivalencia::test_FR233_FR236_*` |
| FR-237, FR-238 (**B-N1**) | H2 esc. 1 a 4 | `test_viaje_rechazo`, `test_viaje_comando::TestComandoRechazado`, `test_viaje_registro::test_FR238_FR252_*` |
| FR-239, FR-240 | H3 esc. 1, 4 | `test_viaje_puerta_cerrada::test_FR239_FR240_*`, `test_FR239_una_puerta_recordada_abierta_que_sigue_abierta_*`; `test_viaje_equivalencia::TestReusoDelCampo` |
| FR-241 (**B-N2**) | H3 esc. 2, 3 | `test_viaje_puerta_cerrada::test_FR239_FR241_APENDICE_B_N2_*`, `test_FR241_FR237_*`, `test_FR241_la_detencion_*` |
| FR-242, FR-243 (**B-N3**) | H4 esc. 1, 2, 5 | `test_viaje_enemigos::test_FR242_FR243_APENDICE_B_N3_*`, `test_FR242_*`, `test_FR243_*` |
| FR-244, FR-245 (**B-N6**) | H4 esc. 3, 4 | `test_viaje_pergamino` (`test_FR244_FR245_APENDICE_B_N6_*`, `test_FR244_un_segundo_*`, `test_FR245_con_el_viaje_aceptado_*`, `test_FR244_despues_*`); `test_viaje_equivalencia::test_FR244_*` |
| FR-246 | H5 esc. 1 a 3 | `test_viaje_antorcha`; `test_viaje_equivalencia::test_FR246_*` |
| FR-247 | H6 esc. 1, 2 | `test_viaje_determinismo::test_FR247_*` |
| FR-248 | H6 esc. 3 | `test_viaje_determinismo::test_FR248_*`, `test_viaje_sin_red` |
| FR-249 | caso límite del enemigo activo, daño y muerte | `test_viaje_enemigos::test_FR249_*` |
| FR-250, FR-251 | — | `python main.py --bench ir_a` (secciones A a H; G para el límite de 5 ms) |
| FR-252 | — | `test_viaje_registro` (marcas, orden, repetición fiel, `historia #k`, `replay hasta`, guardado) |

Casos del Apéndice B: **B-N1** → `test_viaje_rechazo::test_FR237_FR238_APENDICE_B_N1_*`; **B-N2** → `test_viaje_puerta_cerrada::test_FR239_FR241_APENDICE_B_N2_*`; **B-N3** → `test_viaje_enemigos::test_FR242_FR243_APENDICE_B_N3_*`; **B-N6** → `test_viaje_pergamino::test_FR244_FR245_APENDICE_B_N6_*`.

Criterios de éxito: SC-201 → `test_viaje_equivalencia`; SC-202 → `test_viaje_rechazo`; SC-203 → las cuatro pruebas B-N de arriba; SC-204 → `test_viaje_determinismo`; SC-205 → `--bench ir_a` G (400 y 2 000 salas duros; en 20 000 salas el paso sin captura cumple y dos casos informados superan 5 ms, ver `DECISIONES.md`); SC-206 → `test_viaje_ruta::test_FR235_*` y `test_viaje_rechazo` (destinos avistados).

- T048 (2026-11-11): recorrido del quickstart. Pruebas: 56 `test_viaje_*.py` en OK y la suite completa en OK (634 con `requests` disponible; sin él, los mismos 16 módulos de la línea base no importan). Casos B-N1, B-N2, B-N3 y B-N6: una prueba cada uno, en OK. Determinismo y equivalencia: OK. `python main.py --bench ir_a`: CUMPLE (G duro en 400 y 2 000 salas; en 20 000 salas dos casos informados superan 5 ms). Prueba en consola: no se pudo jugar contra el servicio real; se comprobó el comando con el controlador sobre una partida real del modelo (`test_viaje_comando`) y el ciclo registro → archivo de texto → `leer` → repetición con `AlmacenLogTexto` (las marcas `IR_A` y `FIN_IR_A` sobreviven y la repetición es fiel). Laboratorios: prueba_cliente_persistente 23/23, prueba_cliente_offline 13/13, prueba_precarga_presupuesto 24/24, prueba_almacen_disco 40/40, prueba_cliente_http_errores 13/13 y prueba_fabrica 21/21 (con `requests` en una carpeta temporal).
