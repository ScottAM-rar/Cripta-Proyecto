# Contrato: argumentos de línea de comandos y códigos de salida

Cubre FR-301 a FR-305, FR-315 y FR-316.

## 1. Argumentos nuevos

| Argumento | Forma | Efecto |
|---|---|---|
| `--verificar <cripta>` | un valor obligatorio (el id de la cripta) | Verifica la cripta, imprime su reporte y termina sin abrir partida |
| `--forzar` | sin valor | En una partida nueva, permite jugar una cripta no resoluble, con aviso |

Texto de ayuda de `-h` (en español):

- `--verificar CRIPTA`: «verifica si la cripta se puede resolver, muestra el reporte y termina sin abrir la partida (código de salida 0 resoluble, 1 no resoluble, 2 error)»
- `--forzar`: «juega una cripta aunque la verificación diga que no tiene solución (se muestra una advertencia)»

## 2. Códigos de salida de `--verificar`

| Situación | Código | Qué se imprime |
|---|---|---|
| Cripta resoluble | 0 | Reporte `RESOLUBLE` con el orden de obtención de llaves |
| Cripta no resoluble | 1 | Reporte `NO RESOLUBLE` con causas y puertas bloqueadas |
| Cripta inexistente o ilegible, datos no disponibles | 2 | Reporte `NO SE PUDO VERIFICAR` y el motivo |
| Argumento faltante (`--verificar` sin cripta) | 2 | Mensaje de uso de `argparse` en español, a la salida de errores |
| `--verificar` junto con `--replay` o `--bench` | 2 | Una línea que dice qué pasó y qué hacer (usar cada argumento por separado) |
| Error al crear el servicio (`OSError`, `RuntimeError`, `ValueError`) | 2 | `Error: <motivo>` en la salida de errores |

El reporte se imprime **siempre antes de salir**. El texto es el de `ReporteVerificacion.lineas_reporte`, sin cambios. No se crea la vista ni el controlador, no se abre log ni partida. `--forzar` se ignora si viene con `--verificar`. `--offline` y `--cache-size` siguen valiendo.

## 3. Arranque de una partida nueva (sin `--verificar`)

| Situación | Salida en consola | Partida | Código de `main` |
|---|---|---|---|
| Resoluble | reporte (`RESOLUBLE …`) | se abre | 0 al terminar |
| No resoluble, sin `--forzar` | reporte, y debajo la guía de qué hacer | **no** se abre | 1 |
| No resoluble, con `--forzar` | reporte y, aparte, la línea `AVISO: …` de `aviso_forzado` | se abre | 0 al terminar |
| Resoluble, con `--forzar` | reporte; sin aviso de forzar | se abre | 0 al terminar |
| No se pudo verificar | reporte `NO SE PUDO VERIFICAR` y aviso de la 003 | se abre | 0 al terminar |
| Sin criptas disponibles | mensaje «No se encontraron criptas disponibles…» con qué hacer (`pantallas.md` §5) | **no** se abre | 1 |
| Partida cargada de archivo | sin reporte | se abre | 0 al terminar |

Guía de un rechazo (texto exacto en [pantallas.md](pantallas.md) §5).

## 4. Recorrido del valor `forzar` (FR-305)

```text
leer_argumentos(argv).forzar
  → main(): ControladorJuego(servicio, k_checkpoint=…, forzar=args.forzar)
    → ControladorJuego.iniciar(): self.servicio.iniciarJuego(id_cripta, semilla, forzar=self.forzar)
      → EstadoJuegoServicio.iniciarJuego → EstadoJuegoLogica.iniciarJuego(…, forzar=forzar)   [003, sin cambios]
```

Ninguna capa pone `True` o `False` por su cuenta. `--forzar` no se registra en `partida.log` ni en el guardado (FR-304); la reproducción no verifica.

## 5. Lo que no cambia

`--offline`, `--cache-size`, `--bench`, `--bench-csv`, `--replay`, `--hasta`, `--checkpoint-cada`: igual que hoy, incluido el código 130 de Ctrl+C. El mensaje `Error: --hasta requiere --replay` conserva su código 2.
