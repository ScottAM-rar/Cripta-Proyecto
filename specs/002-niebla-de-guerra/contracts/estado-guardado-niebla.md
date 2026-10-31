# Contrato: conocimiento en el estado guardado

**Consume**: Scott, que codifica el formato binario (entrega firme el 9 de noviembre). **Produce**: `Logica/EstadoGuardadoLogica.py` (exportar y restaurar). **Requisitos**: FR-220, FR-221, FR-222.

Este contrato dice **qué conocimiento se guarda** y cómo se valida al cargar. El formato binario en sí es de quien lo codifica.

## 1. Campos nuevos

En `DTO/EstadoGuardadoDTO.py`, el estado guardado gana un campo **al final de la clase** (así lo exige el mecanismo del codec: los campos nuevos van al final):

```text
EstadoGuardadoDTO
  ... campos existentes ...
  conocimiento: ConocimientoGuardadoDTO
```

```text
ConocimientoGuardadoDTO
  exploradas : lista de enteros   # ids de salas exploradas, en ORDEN DE DESCUBRIMIENTO
  avistadas  : lista de enteros   # ids de salas avistadas, en orden ASCENDENTE
  puertas    : lista de PuertaRecordadaDTO   # solo las observadas, ascendente por (sala, direccion)

PuertaRecordadaDTO
  sala      : entero              # id de la sala de origen de la salida
  direccion : entero 0..3         # 0 norte, 1 sur, 2 este, 3 oeste
  cerrada   : booleano            # estado recordado (verdadero = cerrada)
```

Notas:

- **Las salas desconocidas no se guardan**, y tampoco las puertas «sin observar»: lo que no aparece es desconocido o sin observar.
- El **orden de `exploradas` es parte del estado** (es el orden en que se deshace): dos partidas con las mismas acciones producen el mismo orden y, por tanto, archivos idénticos (FR-222).
- `avistadas` se podría derivar de `exploradas` y el esqueleto, pero FR-220 pide guardarla y se usa para detectar archivos incoherentes (§3).
- **Lo que no se guarda**: `version_conocimiento` (es un contador de sesión), `salas_reveladas`/`salidas_examinadas` (estadísticas), el historial del pergamino (ya empieza vacío al cargar) ni los nombres de las salas (salen del esqueleto).
- Dos clases nuevas que el codec debe conocer: `ConocimientoGuardadoDTO` y `PuertaRecordadaDTO`.

## 2. Qué escribe `exportar`

Recorre `exploradas` en su orden; recorre el arreglo de estados una vez para las avistadas (ascendente); recorre las posiciones de puertas con valor distinto de 0 en orden ascendente. Cuesta O(N) por el recorrido de los arreglos; el archivo es de tamaño O(k + observadas).

## 3. Qué valida `restaurar` (antes de tocar la partida)

`restaurar` ya arma todo primero y reemplaza el estado al final; un archivo inválido no deja la partida a medias. Se añade, antes del reemplazo:

| # | Comprobación | Si falla |
|---|---|---|
| V1 | Todo id de `exploradas` y `avistadas` está entre 1 y el mayor id y existe en el esqueleto | `ValueError("conocimiento inválido: ...")` |
| V2 | `exploradas` no repite ids; `avistadas` no repite ids y no comparte ninguno con `exploradas` | ídem |
| V3 | `avistadas` es exactamente el conjunto de salas no exploradas que son destino de una salida de una sala explorada (FR-203) | ídem |
| V4 | La sala actual del jugador está en `exploradas` | ídem |
| V5 | Cada `PuertaRecordadaDTO` nombra una salida que existe en el esqueleto, sin repetir | ídem |

Después carga los arreglos y deja `version_conocimiento` en 0. El historial del pergamino empieza vacío, así que lo restaurado no se puede deshacer.

## 4. Versión y rechazo de archivos anteriores (FR-221)

Un archivo guardado por una versión sin niebla **se rechaza** con un mensaje que indique la versión encontrada y la esperada; no se migra ni se carga. Los mensajes ya existen:

- `AlmacenPartidaBinario`: «Versión del formato de partida no soportada: {encontrada} (este programa usa la {esperada})».
- `EstadoGuardadoLogica.restaurar`: «Versión del estado guardado no soportada: {encontrada!r} (se esperaba {esperada})».

**Pendiente P3 (decisión del grupo con Scott).** Hoy el repositorio declara `VERSION_FORMATO = 6` (por la 001) y `VERSION_ESTADO = 3`. Este contrato exige que un archivo **de la 001 (sin conocimiento) llegue a esos mensajes** y no a un error genérico del decodificador. Eso solo ocurre si el número de versión cambia con esta capacidad. Recomendación: `VERSION_FORMATO = 7` y `VERSION_ESTADO = 4`. Si el grupo decide que el «formato v6» que entrega Scott agrupa 001 y 002 sin haberse liberado antes, entonces un archivo 001-v6 debe rechazarse por otra vía que cite versiones (por ejemplo, un número de versión de estado distinto aunque el de formato no cambie). Cualquiera de las dos cumple FR-221; lo que no se admite es cargar en silencio (constitución VI).

## 5. Qué garantiza a quien consume

1. **Ida y vuelta exacta** (FR-220): `exportar` seguido de `restaurar` deja `estado`, `puertas` y `exploradas` idénticos, incluidos los estados recordados que difieren del real.
2. **Continuación idéntica** (FR-222): una partida guardada y cargada, con las mismas acciones siguientes que una que no se guardó, produce el mismo conocimiento.
3. **Independiente de lo descargado**: el conocimiento no guarda ni lee contenido de salas.

## 6. Pruebas que lo cubren

`test_niebla_guardado.py`: ida y vuelta con salas exploradas, avistadas y una puerta recordada distinta de la real; continuación idéntica; cada comprobación V1 a V5 con un archivo manipulado; rechazo de un archivo de la versión anterior con el mensaje de versión encontrada y esperada.
