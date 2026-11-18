# Contrato de Interfaz CLI: Argumento `--hasta`

Define la sintaxis, validaciones y códigos de salida para la invocación en línea de comandos de la reproducción acotada.

---

## 1. Sintaxis de invocación

```bash
python main.py --replay <PARTIDA.log> [--hasta <t>] [opciones_comunes]
```

### Opciones relevantes

| Opción | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `--replay <PARTIDA.log>` | Archivo en `logs/` | Sí (para `--hasta`) | Indica el archivo de registro a reproducir. |
| `--hasta <t>` | Entero $\ge 0$ | No | Instante del reloj virtual en el que se detiene la reproducción. |
| `--offline` | Bandera booleana | No | Ejecuta sin conectar a la red (comportamiento estándar existente). |
| `--cache-size <N>` | Entero $\ge 1$ | No | Tamaño de la caché en memoria (comportamiento estándar existente). |

---

## 2. Reglas de validación y manejo de errores

### 2.1 Argumento `--hasta` sin `--replay` (FR-408)

Si se invoca `--hasta` en ausencia de `--replay`:

- **Comportamiento**: El programa finaliza de inmediato sin crear instancias de `EstadoJuegoServicio`, sin inicializar adaptadores y sin leer archivos.
- **Canal de salida**: `stderr`
- **Mensaje exacto**:
  ```text
  Error: el argumento --hasta requiere especificar una partida con --replay.
  ```
- **Código de salida**: `2`

### 2.2 Valor no entero para `t` (FR-407)

Si el valor pasado a `--hasta` no es convertible a un número entero (ej. `abc`, `12.5`, `none`):

- **Comportamiento**: `argparse` rechaza el argumento mediante la función validadora `_instante_hasta`.
- **Canal de salida**: `stderr`
- **Mensaje**:
  ```text
  usage: main.py [-h] [--offline] [--cache-size N] [--bench [BLOQUES]] [--bench-csv ARCHIVO.csv] [--replay PARTIDA.log] [--hasta T]
  main.py: error: argument --hasta: 'abc' no es un número entero
  ```
- **Código de salida**: `2`

### 2.3 Valor negativo para `t` (FR-407)

Si el valor pasado a `--hasta` es un entero estrictamente menor que 0 (ej. `-1`, `-50`):

- **Comportamiento**: `_instante_hasta` rechaza el valor.
- **Canal de salida**: `stderr`
- **Mensaje**:
  ```text
  usage: main.py [-h] [--offline] [--cache-size N] [--bench [BLOQUES]] [--bench-csv ARCHIVO.csv] [--replay PARTIDA.log] [--hasta T]
  main.py: error: argument --hasta: el instante virtual debe ser mayor o igual que 0
  ```
- **Código de salida**: `2`

### 2.4 Invocación exitosa (FR-401, FR-409, FR-410)

- Con `--replay ARCHIVO.log --hasta t`: Ejecuta la reproducción hasta $t$, muestra el estado exhaustivo en `stdout` y finaliza con código de salida `0`.
- Con `--replay ARCHIVO.log` (sin `--hasta`): Conserva el formato exacto existente y finaliza con código de salida `0`.
- No se crea ninguna ventana visual ni interfaz gráfica en ningún caso.
