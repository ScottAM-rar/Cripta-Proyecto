# Modelo de datos: Comando «ir a»

**Carpeta**: `006-ir-a` | Nada de esto se guarda en la partida (decisión D8): son datos de ejecución.

## Viaje (`ViajeLogica`)

Objeto transitorio de la lógica; a lo más uno por partida.

| Campo | Significado | Regla |
|---|---|---|
| `destino` | id de la sala a la que se viaja | explorada al iniciar (FR-231, FR-237) |
| `estado` | `EN_CURSO`, `LLEGADO`, `DETENIDO` o `RECHAZADO` | transiciones abajo |
| `motivo` | por qué terminó o se rechazó (ver tabla de motivos) | `None` mientras `EN_CURSO` y cuando `LLEGADO` |
| `pasos` | cantidad de pasos dados | sube en 1 por movimiento aceptado |
| `tiempo` | suma de lo que avanzó el reloj durante los pasos | informativo: es la diferencia de reloj, no un contador aparte |
| `version_vista` | `version_conocimiento` con la que se calculó el campo | si difiere de la actual, se recalcula (D3) |
| `buscador` | el `BuscadorRutas` con el campo hacia `destino` | uno por viaje; no se guarda la ruta |
| `vista` | `VistaMapaConocido` del conocimiento | la de la lógica; no se copia |

### Transiciones

```text
(orden) ──rechazo──► RECHAZADO            sin efecto alguno (FR-237, FR-238)
(orden) ──aceptada─► EN_CURSO ──paso──► EN_CURSO
                       EN_CURSO ──llega al destino──────────► LLEGADO
                       EN_CURSO ──muerte / daño / enemigos / sin ruta──► DETENIDO(motivo)
                       EN_CURSO ──pergamino (aviso de accionJugador)──► DETENIDO(PERGAMINO)
```

Todo estado distinto de `EN_CURSO` es final: no se reanuda (supuesto del spec).

### Motivos

| Motivo | Estado | Origen | Texto para el jugador |
|---|---|---|---|
| `DESTINO_INEXISTENTE` | `RECHAZADO` | FR-237 | «No existe esa sala.» |
| `NO_EXPLORADO` | `RECHAZADO` | FR-237 | «Esa sala no está explorada.» |
| `SIN_RUTA_INICIAL` | `RECHAZADO` | FR-237 | «No hay ruta conocida hasta esa sala.» |
| `YA_ESTAS_ALLI` | `RECHAZADO` | FR-231 | «Ya estás en esa sala.» (sin tiempo ni acción) |
| `SIN_RUTA` | `DETENIDO` | FR-241 | «Una puerta que recordabas abierta está cerrada y no hay otra ruta conocida.» |
| `ENEMIGOS_DORMIDOS` | `DETENIDO` | FR-243 | «Entraste a una sala con enemigos dormidos y se despertaron.» |
| `ENEMIGO_ACTIVO` | `DETENIDO` | FR-249a | «Un enemigo activo está en la sala.» |
| `DANO` | `DETENIDO` | FR-249b | «Recibiste daño.» |
| `MUERTE` | `DETENIDO` | FR-249c | «Moriste durante el viaje.» |
| `PERGAMINO` | `DETENIDO` | FR-245 | «El pergamino canceló el viaje.» |
| `FIN_PARTIDA` | `DETENIDO` | defensa | «La partida terminó.» |
| `MOVIMIENTO_RECHAZADO` | `DETENIDO` | defensa (D3) | «No se pudo dar el siguiente paso.» |
| `CANCELADO_POR_JUGADOR` | `DETENIDO` | `cancelarViaje` (solo pruebas) | «Viaje cancelado.» |

`YA_ESTAS_ALLI` es un rechazo (no consume ni cuenta como acción, FR-238) para que el caso «ya estoy allí» tenga un único comportamiento.

## Resultado del viaje (`ResultadoViajeDTO`)

Datos simples que cruzan Servicio → Controlador → Vista (el modelo no conoce la vista).

| Campo | Tipo | Contenido |
|---|---|---|
| `estado` | texto | `LLEGADO`, `DETENIDO` o `RECHAZADO` (o `EN_CURSO` en la API paso a paso) |
| `motivo` | texto o `None` | uno de la tabla de motivos |
| `mensaje` | texto | el texto del jugador |
| `sala_final` | entero | sala del jugador al terminar |
| `pasos` | entero | pasos dados |
| `tiempo` | entero | unidades de reloj consumidas por los pasos |
| `recorrido` | lista de enteros | ids de las salas en que entró, en orden |

`recorrido` es una lista creada por el viaje (no una estructura de búsqueda). Es la secuencia observable que usan las pruebas de determinismo.

## Marcas del log (ver [contracts/registro-viaje.md](contracts/registro-viaje.md))

| Marca | Campos | Cuándo |
|---|---|---|
| `IR_A` | destino | al aceptar la orden, antes del primer paso |
| `FIN_IR_A` | resultado, motivo, sala final | al llegar, detenerse o cancelarse |

## Contadores de ejecución nuevos en la lógica

| Campo | Para qué | Se guarda |
|---|---|---|
| `viaje_activo` | el viaje `EN_CURSO` o `None`; `accionJugador` lo avisa del pergamino | No; se pone en `None` al iniciar, restaurar y cargar |
| `activaciones_enemigos` | entero que sube cuando `_activarEnemigos` despierta a un enemigo; el viaje lo compara antes y después de un paso | No; no se deshace (solo se compara dentro de un paso) |

## Lo existente que se lee (no se modifica)

| Dato | Dónde | Uso |
|---|---|---|
| Estado de cada sala (explorada, avistada, desconocida) | `MapaConocido.estado` | Validar el destino (FR-237) |
| Puertas recordadas | `MapaConocido.puertas` | Solo a través de `VistaMapaConocido.transitable` |
| `version_conocimiento` | `MapaConocido` | Decidir si se recalcula |
| Costo de cada salida | aristas del esqueleto (`MapaCripta`) | Costo de la ruta y de cada paso |
| Enemigos de la sala actual | `SalaDTO.enemigos` | Comprobar `ENEMIGO_ACTIVO` |
