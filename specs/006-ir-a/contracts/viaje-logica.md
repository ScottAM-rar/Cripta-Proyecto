# Contrato: orquestador del viaje y servicio

**Produce**: `Logica/ViajeLogica.py`, `DTO/ResultadoViajeDTO.py`, y en `Servicio/EstadoJuegoServicio.py` las operaciones `irA`, `iniciarViaje`, `avanzarViaje` y `cancelarViaje`. **Requisitos**: FR-231 a FR-251.

## 1. Interfaz de `ViajeLogica`

El viaje recibe la lógica del juego (acceso a `accionJugador`, `ingresarEnSala`, el conocimiento y el log); no importa red, disco ni vista.

| Operación | Efecto | Resultado |
|---|---|---|
| `iniciar(destino)` | Valida la orden y, si procede, calcula el campo de costos y queda `EN_CURSO` | `ResultadoViajeDTO` `RECHAZADO` (sin efecto alguno) o `EN_CURSO` (escribe la marca `IR_A`) |
| `avanzar()` | Da **un** paso (o termina el viaje) | `ResultadoViajeDTO` con el estado tras el paso |
| `ejecutar()` | Repite `avanzar()` hasta que el estado deje de ser `EN_CURSO` | `ResultadoViajeDTO` final |
| `cancelar(motivo)` | Pasa a `DETENIDO(motivo)` y escribe `FIN_IR_A`; no hace nada si el viaje ya terminó | — |

## 2. `iniciar(destino)`

Orden de comprobaciones; la primera que falla rechaza **sin tocar nada** (FR-238):

1. El juego está iniciado y no terminó (igual que cualquier acción: `ValueError` en caso contrario).
2. `destino` es un entero dentro de las salas de la cripta, si no `DESTINO_INEXISTENTE`.
3. El estado de conocimiento del destino es *explorada*, si no `NO_EXPLORADO`.
4. El destino no es la sala del jugador, si no `YA_ESTAS_ALLI`.
5. Con el campo calculado, `costo(sala_actual)` no es `None`, si no `SIN_RUTA_INICIAL`.

Si pasa todo: escribe `IR_A`, guarda `version_vista` y queda `EN_CURSO` sin haber dado ningún paso.

## 3. `avanzar()`

1. Si el viaje no está `EN_CURSO`, devuelve su resultado final sin hacer nada.
2. Si `version_conocimiento` ≠ `version_vista`, recalcula el campo y actualiza `version_vista` (D3).
3. Si `costo(sala_actual)` es `None`: `DETENIDO(SIN_RUTA)`, escribe `FIN_IR_A`, **no da el paso**.
4. `arista = siguiente_paso(sala_actual)` (desempate de FR-234).
5. Construye `EventoDTO(costo de la salida, 0, jugador, "MOVER_JUGADOR", [sala_actual, dirección])` y llama `accionJugador`. Si el resultado no fue exitoso: `DETENIDO(MOVIMIENTO_RECHAZADO)` sin tiempo.
6. Llama `ingresarEnSala(sala nueva)` (activa enemigos dormidos, §2.4), anota la sala en `recorrido`, sube `pasos`.
7. Evalúa, en este orden, MUERTE → LLEGADA → DANO → ENEMIGOS_DORMIDOS → ENEMIGO_ACTIVO ([research.md](../research.md) D4). Si ninguna se cumple, sigue `EN_CURSO`.
8. Al terminar (cualquier motivo) escribe `FIN_IR_A`.

Garantías:

- **Un paso = un movimiento normal**: mismo evento, mismo reloj, mismas trampas, misma antorcha, misma observación de puertas y mismo registro que caminar a mano (FR-233, FR-236).
- **Sin tiempo en los rechazos y las detenciones previas al paso** (FR-238, FR-241).
- **Solo conocimiento**: la ruta usa `VistaMapaConocido` y el costo de cada paso es el de la salida (FR-235). No lee el contenido de salas no visitadas (FR-248).
- **Determinista**: el único desempate es el menor id (FR-234); sin azar ni hora.

## 4. Aviso del pergamino

`accionJugador` llama a `viaje_activo.cancelar("PERGAMINO")` justo después de procesar un uso de pergamino, si hay un viaje `EN_CURSO` (FR-244, FR-245). `cancelar` no vuelve a calcular nada. Después de cancelar, `viaje_activo` es `None`.

## 5. Servicio

| Operación | Comportamiento |
|---|---|
| `irA(destino) -> ResultadoViajeDTO` | `iniciar` + `ejecutar`; es lo que usa el comando de consola |
| `iniciarViaje(destino) -> ResultadoViajeDTO` | Solo `iniciar`; deja el viaje `EN_CURSO` para usar `avanzarViaje` |
| `avanzarViaje() -> ResultadoViajeDTO` | Un paso; para pruebas, la API falsa de la 009 y `--bench` |
| `cancelarViaje()` | Cancela con el motivo `CANCELADO_POR_JUGADOR` (no existe en la consola; sirve a las pruebas) |

Ninguna crea una acción propia: lo que consume tiempo o llega al historial son los pasos, que son movimientos.

## 6. Qué NO hace

- No guarda un viaje en curso ni cambia el formato de partida (D8).
- No encadena destinos ni reanuda viajes cancelados.
- No modifica `BuscadorRutas` ni `VistaMapaConocido`.

## 7. Pruebas que lo cubren

| Prueba | Cubre |
|---|---|
| `test_viaje_ruta.py` | Ruta de menor costo, empates (FR-234), `YA_ESTAS_ALLI`, ruta que evita puertas recordadas cerradas o sin observar (FR-235), tiempo = suma de costos (FR-236) |
| `test_viaje_rechazo.py` | **B-N1** y los otros rechazos: reloj, conocimiento, log y pergamino idénticos (FR-237, FR-238) |
| `test_viaje_puerta_cerrada.py` | **B-N2**: recálculo con alterna, y sin alterna se detiene sin tiempo adicional (FR-239 a FR-241) |
| `test_viaje_enemigos.py` | **B-N3**: activación §2.4 y detención; destino con dormidos; sala sin enemigos no detiene; enemigo activo, daño y muerte (FR-242, FR-243, FR-249) |
| `test_viaje_pergamino.py` | **B-N6**: revierte solo el último paso y cancela; segundo pergamino revierte el paso anterior (FR-244, FR-245) |
| `test_viaje_antorcha.py` | Cada entrada explora vecinas como a mano; las nuevas sirven al recálculo (FR-246) |
| `test_viaje_determinismo.py` | Mismo viaje con y sin contenido descargado, y con guardar/cargar a mitad (FR-247, FR-248) |
| `test_viaje_equivalencia.py` | Viajar = caminar la misma ruta a mano; reutilizar el campo = recalcular cada paso (constitución III) |
| `test_viaje_registro.py` | Marcas `IR_A`/`FIN_IR_A`, repetición fiel, `historia #k` y `replay hasta` a mitad de un viaje (FR-252) |
| `test_viaje_sin_red.py` | 0 solicitudes nuevas (FR-248, principio VI) |
