# Contrato: interfaz de la verificación para otras capacidades

Lo que consume Fernanda para conectar `--verificar` y `--forzar` en `main.py` y en la vista. Esta capacidad **no** cablea esas opciones. El primer grupo de tareas entrega todo esto con cuerpo provisional ([../research.md §12](../research.md)); después solo cambia el comportamiento, no las firmas.

## Operación pública (capa Servicio)

```python
# Servicio/EstadoJuegoServicio.py
def verificar(self, cripta_id: str, offline: bool | None = None) -> ResultadoVerificacion: ...
def iniciarJuego(self, cripta: str, semilla=None, offline: bool | None = None,
                 nombre_log: str | None = None, forzar: bool = False) -> None: ...
def avisoResolubilidad(self) -> str | None: ...
```

| Operación | Comportamiento |
|---|---|
| `verificar(cripta_id)` | No inicia partida, no crea log, no usa la vista (FR-330). Delega en `Logica.VerificacionResolubilidad.verificar(fuente, cripta_id)`. Nunca lanza por falta de datos: devuelve `resoluble=None` con `motivo_error` (FR-343). Solicitudes: a lo sumo las de datos generales y esqueleto (si no están guardados) y la única consulta de llaves de la 009 (FR-341) |
| `iniciarJuego(..., forzar=False)` | Como hoy, más la verificación de [../research.md §7](../research.md). Cripta no resoluble sin `forzar`: lanza `CriptaNoResoluble` **antes** de abrir el log (FR-339). Con `forzar`: inicia (FR-340) |
| `avisoResolubilidad()` | `None` si no hay partida o no hay aviso; si no, el texto a mostrar **una vez al iniciar**, igual que `avisoLlaves()` (clarificación Q3) |

## Funciones de Logica

```python
# Logica/VerificacionResolubilidad.py
def verificar_resolubilidad(mapa: MapaCripta, sala_inicial: int, sala_salida: int,
                            llave_salida: str | None, llaves: UbicacionLlavesDTO,
                            cripta_id: str = "") -> ResultadoVerificacion: ...
def verificar(fuente: FuenteCripta, cripta_id: str,
              llaves: UbicacionLlavesDTO | None = None) -> ResultadoVerificacion: ...
class CriptaNoResoluble(RuntimeError):
    resultado: ResultadoVerificacion

# Logica/ReporteVerificacion.py
def lineas_reporte(resultado: ResultadoVerificacion) -> list[str]: ...
def aviso_forzado(resultado: ResultadoVerificacion) -> str: ...
```

- `verificar_resolubilidad` es pura: no hace E/S ni solicitudes; mismo resultado para los mismos datos (FR-335).
- `verificar` junta los datos con `fuente.existe_cripta`, `obtener_mapa`, `obtener_sala_inicial`, `obtener_sala_salida`, `obtener_llave_salida` y, si `llaves` es `None`, `ubicacion_llaves`. Traduce los fallos según [../research.md §8](../research.md).

## Uso esperado en `main.py` (lo escribe Fernanda; aquí solo como referencia del contrato)

```text
--verificar <cripta>:   r = servicio.verificar(cripta)
                        imprimir cada línea de lineas_reporte(r)
                        salir con r.codigo_salida()          # 0 / 1 / 2
partida sin --forzar:   servicio.iniciarJuego(...); si lanza CriptaNoResoluble, imprimir str(error) y salir con 1
partida con --forzar:   servicio.iniciarJuego(..., forzar=True); mostrar avisoResolubilidad() si no es None
```

## Entrega provisional (primer grupo de tareas)

| Pieza | Estado provisional |
|---|---|
| `ResultadoVerificacion`, `PasoLlaveDTO`, `BloqueoDTO`, `codigo_salida()` | Definitivos |
| `verificar_resolubilidad`, `verificar` | Devuelven `resoluble=None`, `motivo_error="La verificación de resolubilidad todavía no está implementada."` |
| `CriptaNoResoluble` | Definitiva (todavía nadie la lanza) |
| `lineas_reporte`, `aviso_forzado` | Formatean el caso de error; los otros casos se completan con el algoritmo |
| `EstadoJuegoServicio.verificar`, `avisoResolubilidad`, parámetro `forzar` | Firmas definitivas; `forzar` se acepta sin efecto |

Una prueba de contrato (`test_resolubilidad_reporte.py`, clase `Contrato`) fija estas firmas desde la entrega provisional.
