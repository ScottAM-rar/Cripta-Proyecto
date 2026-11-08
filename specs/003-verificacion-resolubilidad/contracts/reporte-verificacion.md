# Contrato: texto del reporte y códigos de salida

Un solo lugar: `Logica/ReporteVerificacion.py` (`lineas_reporte`, `aviso_forzado`). El texto se arma **solo** con el `ResultadoVerificacion`, así que dos resultados iguales dan reportes idénticos carácter por carácter (FR-335). Sin fecha, hora, rutas ni contadores de solicitudes.

## Códigos de salida de `--verificar` (FR-331)

| Código | Cuándo |
|---|---|
| 0 | `resoluble is True` |
| 1 | `resoluble is False` |
| 2 | `resoluble is None` (error de datos, FR-343) |

## Forma del reporte

Los ejemplos usan `cripta-01`, el id que publica siempre la API falsa v2 (`HttpConfigurable`), así que las pruebas pueden compararlos literalmente.

Resoluble (B-R3):

```text
Verificación de la cripta cripta-01: RESOLUBLE.
Orden de obtención de llaves:
  1. itm_llave_a en la sala 2
  2. itm_llave_b en la sala 3
  3. itm_llave_salida en la sala 5 (llave de salida)
```

Con enemigo (B-R2): `  1. itm_llave_salida en la sala 3, la suelta e-errante (llave de salida)`.

No resoluble (B-R1):

```text
Verificación de la cripta cripta-01: NO RESOLUBLE.
Motivo: la sala de salida 2 tiene camino, pero las puertas lo impiden.
Puertas bloqueadas:
  - Sala 1, salida este hacia la sala 2: pide itm_llave_salida (llave de salida), que está en la sala 2. Ciclo: la llave está detrás de esta puerta o de otras puertas bloqueadas.
Salas alcanzables (1): 1
Salas no alcanzables: 1
```

No resoluble (B-R4): la puerta dice `pide itm_llave_perdida, que no existe en la cripta.`

Error de datos:

```text
Verificación de la cripta cripta-01: NO SE PUDO VERIFICAR.
<motivo_error>
```

## Textos fijos por causa y por tipo de bloqueo

| Clave | Texto |
|---|---|
| `LLAVE_SALIDA_INEXISTENTE` | `la llave de salida <id> no existe en la cripta.` |
| `SALIDA_SIN_CAMINO` | `la sala de salida <n> no tiene camino desde la sala inicial, aunque se tuvieran todas las llaves.` |
| `SALIDA_BLOQUEADA` | `la sala de salida <n> tiene camino, pero las puertas lo impiden.` |
| `LLAVE_SALIDA_INALCANZABLE` | `se llega a la sala de salida <n>, pero la llave de salida <id> no se puede obtener.` |
| `SIN_LLAVE` | `está cerrada y no tiene llave.` |
| `LLAVE_INEXISTENTE` | `pide <id>, que no existe en la cripta.` |
| `CICLO` | `pide <id>, que está en la(s) sala(s) <lista>. Ciclo: la llave está detrás de esta puerta o de otras puertas bloqueadas.` |
| `LLAVE_SIN_CAMINO` | `pide <id>, que está en la(s) sala(s) <lista>, sin camino desde la sala inicial.` |

Varias causas: una línea `Motivo:` por causa, en el orden de `causas`. Listas de salas separadas por coma y espacio. La llave de salida se marca con ` (llave de salida)` donde aparezca.

## Aviso de `--forzar` (FR-340, clarificación Q3)

`aviso_forzado(resultado)` devuelve una sola línea, que el controlador muestra **solo al iniciar**:

```text
AVISO: la cripta X no es resoluble (<primera causa>); la partida se inicia porque se usó --forzar.
```

Los textos exactos se fijan en `test_resolubilidad_reporte.py`; si cambian, cambian la prueba y este contrato en la misma tarea.
