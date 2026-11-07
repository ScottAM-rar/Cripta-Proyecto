# Contrato: clientes, servicio de cripta, fuente solo local y fábrica

## `ClienteInterfaz.obtener_llaves(cripta_id, solo_guardadas=False) -> list[dict]`

| Implementación | `solo_guardadas=False` | `solo_guardadas=True` | Solicitudes |
|---|---|---|---|
| `ClienteCripta` (HTTP) | `leer_llaves(_solicitar("/criptas/<id>/llaves"))`. Si no hay conexión, `ErrorSinConexion`; con otro código HTTP, `RuntimeError` | `LlavesNoDisponibles` (no hay disco) | 1 (más los 429) |
| `ClientePersistente` | `_asegurar_cripta` → si `leer_llaves` no es `None`, devuelve eso. Si es `None`: HTTP, `validar_llaves` con `leer_salas`/`leer_contenido` del disco y, **solo si es válida**, `guardar_llaves` | Lo guardado, o `LlavesNoDisponibles("sin presupuesto")` | 0 si estaba guardado; 1 si no |
| `ClienteOffline` | Lo guardado, o `ErrorOffline("Faltan las llaves de la cripta X")` | Igual | 0 |
| `HttpFalso` / `HttpConfigurable` (v2) | Llaves configuradas, o el fallo configurado | — (lo resuelve el persistente que lo envuelve) | 1 por llamada |

## `ServicioCripta` (AMPLIADO)

```text
esqueleto(cripta_id) -> MapaDTO
    # Esqueleto normalizado con costos (capacidad 001). obtener_mapa(cripta_id) devuelve esqueleto(cripta_id).

ubicacion_llaves(cripta_id) -> UbicacionLlavesDTO
    # 1. Si ya la tiene memorizada para esta cripta, la devuelve (FR-301).
    # 2. solo_guardadas = presupuesto_solicitudes(cripta_id) - solicitudes_realizadas < 1
    # 3. crudas = cliente.obtener_llaves(cripta_id, solo_guardadas)
    # 4. validar_llaves(crudas, existe del esqueleto, contenido_guardado del cliente, si lo hay)
    # 5. Memoriza y devuelve el DTO.
    # Cualquier ErrorOffline, ErrorSinConexion, RuntimeError HTTP o LlavesInvalidas se convierte en
    # LlavesNoDisponibles(mensaje con la cripta y el motivo). No queda nada memorizado tras un fallo.
```

## `EstadoJuegoLogica.iniciarJuego` (AMPLIADO)

Después de `total_salas`:

```text
try:   self.llaves = comunicacion.ubicacion_llaves(cripta); self.avisoLlaves = None
except LlavesNoDisponibles as e: self.llaves = None; self.avisoLlaves = str(e)
```

La vista muestra `avisoLlaves` al empezar, si lo hay. `--verificar` (capacidad 003) debe terminar con error si `llaves is None` (FR-313); esta capacidad solo deja disponibles el estado y el mensaje.

## `FuenteSoloLocal` (`adaptadores/fuente_solo_local.py`)

```text
FuenteSoloLocal(fuente: ServicioCripta, almacen: AlmacenDisco, version_vigente: str)
```

- Cada operación primero comprueba `almacen.version_cripta(id) == version_vigente`; si no coincide, lanza `DatoLocalFaltante`.
- `ErrorOffline` y `LlavesNoDisponibles` del interior se convierten en `DatoLocalFaltante(dato, cripta)`.
- Nunca llama a `validar_cripta`, porque vaciaría el archivo, ni a ningún método de escritura.

## `fabrica` (AMPLIADO)

```text
crear_servicio(...)                                         # sin cambios de firma
crear_fuente_solo_local(carpeta=CARPETA_DATOS, version_vigente=None) -> FuenteSoloLocal
    # version_vigente None: se usa la versión guardada (útil para pruebas); la capacidad 004 pasa la del log.
```

## `resolucion` (AJUSTE)

No cambia lo que ya hace. `contenido_guardado` se obtiene con un método opcional del cliente, `contenido_en_disco(cripta_id, sala) -> dict | None`, que implementan el persistente y el offline (leen `AlmacenDisco.leer_contenido`) y que el HTTP no tiene. `ServicioCripta` lo busca con `getattr`, igual que el modelo busca `obtener_mapa`.
