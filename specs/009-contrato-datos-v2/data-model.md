# Modelo de datos (Fase 1): Contrato de datos v2 y ubicación de llaves

Solo lo que se agrega o cambia. Lo que no aparece aquí (Parte I, capacidades 001 y 005) no cambia.

## UbicacionLlavesDTO (`DTO/LlavesDTO.py`, NUEVO)

Lo que el modelo recibe de `FuenteCripta.ubicacion_llaves`. Son **listas paralelas**: la posición `i` describe una ubicación. No hay `dict` ni `set`.

| Campo | Tipo | Regla |
|---|---|---|
| `cripta_id` | `str` | Cripta de la que salen las llaves |
| `version` | `str \| None` | Versión de la cripta con la que se obtuvieron |
| `ids` | `list[str]` | Id de catálogo de la llave (por ejemplo, `itm_llave_bronce`). **Puede repetirse** con otra sala o con otro enemigo (FR-302) |
| `salas` | `list[int]` | Si `enemigos[i]` es `None`, la sala donde está la llave; si no, la sala donde inicia ese enemigo |
| `enemigos` | `list[str \| None]` | `instancia` del enemigo que suelta la llave, o `None` si la llave está en el suelo |

**Invariantes**: `len(ids) == len(salas) == len(enemigos)`. No hay dos posiciones con la misma terna. El orden es el de la respuesta del servicio y se conserva tal cual, para que dos ejecuciones entreguen la misma secuencia (principio II).

**Operaciones** (sin índices):

| Operación | Costo | Uso |
|---|---|---|
| `cantidad()` | O(1) | — |
| `ubicaciones_de(id_llave) -> list[int]` | O(k) | Posiciones de una llave. La capacidad 003 arma su propio índice si lo necesita |

Lista vacía (`cantidad() == 0`): es válida y significa que la cripta no tiene llaves.

## Errores del contrato del modelo (`Logica/FuenteCripta.py`, AMPLIADO)

| Error | Hereda de | Cuándo | Mensaje (debe nombrar la cripta) |
|---|---|---|---|
| `LlavesNoDisponibles` | `RuntimeError` | El servicio no responde, la respuesta es inválida, no queda presupuesto, o en `--offline` faltan las llaves (FR-309 a FR-312) | «No se pudieron obtener las llaves de la cripta X: <motivo>. La verificación de resolubilidad no está disponible.» |
| `DatoLocalFaltante` | `RuntimeError` | En la lectura solo local falta un dato o tiene otra versión (FR-315, FR-317) | «Falta en disco <dato> de la cripta X» o «La cripta X está guardada con la versión v1; se necesita v2» |

Se definen en el contrato del modelo para que `EstadoJuegoLogica` los capture sin importar adaptadores (principio IV).

`LlavesInvalidas(motivo)` es interno de los adaptadores (`adaptadores/llaves.py`). `ServicioCripta` lo traduce siempre a `LlavesNoDisponibles`.

## FuenteCripta (`Logica/FuenteCripta.py`, AMPLIADO)

```text
esqueleto(cripta_id) -> MapaDTO                   # NUEVO (obtener_mapa delega en este)
ubicacion_llaves(cripta_id) -> UbicacionLlavesDTO # NUEVO; lanza LlavesNoDisponibles
```

## ClienteInterfaz (`adaptadores/Interfaz.py`, AMPLIADO)

```text
obtener_llaves(cripta_id: str, solo_guardadas: bool = False) -> list[dict]
```

Devuelve la lista cruda de la respuesta (cada elemento con `id`, `sala` y opcionalmente `enemigo`). Detalle por implementación en [contracts/interfaz-clientes.md](contracts/interfaz-clientes.md).

## Archivo de la cripta en disco (`datos_cripta/cripta_<id>.bin`, AMPLIADO)

| Clave | Valor | Estado |
|---|---|---|
| `version` | `str` | Existente |
| `datos` | respuesta de `/criptas/<id>` | Existente |
| `salas` | esqueleto | Existente |
| `contenido:<n>` | contenido de la sala n | Existente |
| **`llaves`** | `list[dict]`: la lista cruda **ya validada** | **NUEVA** |

**Ciclo de vida de `llaves`**:

```text
ausente ──(consulta OK y validada)──▶ guardada (versión v)
guardada ──(se inicia con la versión v)──▶ guardada (sin solicitudes)
guardada ──(se inicia con otra versión)──▶ ausente  (_validar vacía el archivo completo)
ausente ──(fallo o respuesta inválida)──▶ ausente  (no se escribe nada, FR-310)
```

Un archivo de la Parte I no tiene la clave: está en el estado «ausente». No hace falta cambiar `VERSION_FORMATO` de `ArchivoIndexado`, porque agregar una clave no rompe a quien lee las demás.

`AlmacenDisco` gana dos métodos: `guardar_llaves(cripta_id, llaves)` y `leer_llaves(cripta_id) -> list[dict] | None`. `None` significa ausente; `[]` significa cripta sin llaves.

## Estado de la partida (`EstadoJuegoLogica`, AMPLIADO)

| Campo | Tipo | Regla |
|---|---|---|
| `llaves` | `UbicacionLlavesDTO \| None` | `None` en `__init__` y al restaurar una partida guardada. Lo llena `obtenerLlaves()`: en una partida nueva, desde `iniciarJuego`; en una partida cargada, la primera vez que se necesita (FR-325). Sigue en `None` si hubo `LlavesNoDisponibles` |
| `avisoLlaves` | `str \| None` | `None` en `__init__` y al restaurar. Mensaje del último `LlavesNoDisponibles`, para mostrarlo (FR-313) |

**Operación**: `obtenerLlaves() -> UbicacionLlavesDTO | None`. Si `llaves` no es `None`, la devuelve sin pedir nada. Si no, pide `ubicacion_llaves(idCripta)` a la fuente (buscada con `getattr` por compatibilidad con fuentes de prueba antiguas; sin el método devuelve `None` sin aviso). Ante `LlavesNoDisponibles` guarda el aviso y devuelve `None`. El fallo no se memoriza: otra llamada vuelve a pedir, y la fuente decide con lo guardado y el presupuesto si hace la solicitud.

**Ciclo de vida en la partida**:

```text
__init__ / restaurar ─▶ llaves=None, aviso=None
iniciarJuego (nueva) ──▶ obtenerLlaves()
obtenerLlaves() ──(guardadas, misma versión)──▶ llaves (0 solicitudes)
obtenerLlaves() ──(faltan, queda presupuesto)──▶ llaves (1 solicitud, la única de la cripta)
obtenerLlaves() ──(faltan, sin presupuesto o fallo)──▶ llaves=None, aviso (FR-313)
```

**No forman parte del estado guardado ni del `partida.log`**: se derivan de la cripta y su versión, que ya están en el encabezado. Así el formato de partida no cambia, ya que el v6 es de la capacidad 010, y el determinismo no depende de si había red.

## FuenteSoloLocal (`adaptadores/fuente_solo_local.py`, NUEVO)

| Campo | Tipo | Regla |
|---|---|---|
| `fuente` | `ServicioCripta` sobre `ClienteOffline` | Lo arma `fabrica.crear_fuente_solo_local` |
| `almacen` | `AlmacenDisco` | Solo se lee |
| `version_vigente` | `str` | Versión contra la que se compara lo guardado (FR-317) |

Implementa las operaciones de `FuenteCripta` que lee la consulta histórica: `esqueleto`, `construir_sala`, `ubicacion_llaves`, `datos_cripta`, `crear_jugador`, `version_cripta` y `total_salas`. `precargar_vecinas` devuelve 0. `reporte()` muestra 0 solicitudes.

## Informe de medición (`bench/llaves.py` → `mediciones.md`)

| Campo | Contenido |
|---|---|
| tamaño, semilla, cazadores | parámetros de la cripta sintética |
| regla | `saltos` \| `costo` |
| `solicitudes_totales` | solicitudes de la partida guionada |
| `solicitudes_por_cazador` | solicitudes de contenido disparadas por cargas iniciadas por un enemigo |
| recomendación | texto en `mediciones.md` |
