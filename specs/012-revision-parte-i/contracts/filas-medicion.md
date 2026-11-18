# Contrato: filas de los bloques `cache` y `guardado`, y formato de `mediciones.md`

## Catálogo de filas

El número de fila es estable y empareja M0, M1 y M2. Se toma del orden de salida del bloque en M0 y se agregan al final las filas nuevas. Si M0 muestra más o menos filas que esta tabla, gana M0 y la tabla se ajusta en `mediciones.md`.

### Bloque `cache` (`python main.py --bench cache`)

| Filas | Sección | Medición | Tipo | Carga que recibe (research D3) |
|---|---|---|---|---|
| 1–4 | 1. Solicitudes al recorrer un pasillo de 60 salas | sala por sala; actual + vecinas (prof. 2); perezosa (prof. 2); perezosa por defecto | cuenta | costos de salida, +1 consulta de llaves y cazadores que se mueven (las solicitudes disparadas van en la unidad) |
| 5–16 | 2. Búsqueda en la caché (µs) | por tamaño (25, 100, 1 000 y 5 000): lineal con acierto, lineal con fallo y tabla hash propia (descartada). En M2, «deque lineal» pasa a llamarse «lista propia lineal» | tiempo | no aplica (operación aislada) |
| 17–19 | 3. Recuperar una ficha liberada desde disco | catálogo de 25, 200 y 1 000 fichas | tiempo | fichas de la Parte II (incluye una de cazador) |
| 20–22 | 4. Guardar 10 fichas nuevas | catálogo de 25, 200 y 1 000 fichas | tiempo | igual que la 3 |
| 23–25 | 5. Planear la vecindad en 1 000 salas | `salas_vecinas` a 1 y 2 pasos; `precargar_vecinas` sin nada que hacer | tiempo | esqueleto con costos |
| 26–30 | 6. Caché en una partida completa | capacidad 5, 10, 25, 100 y 1 000: aciertos/fallos (%) y solicitudes | cuenta | costos, +1 llaves, cazadores que se mueven (también en el contenido y el catálogo) |
| 31–34 | 2. (nueva) | lista enlazada propia (descartada), acierto, por tamaño | tiempo | no aplica; sin antes en M0 ni en M1 si el prototipo se agrega con D2 |

### Bloque `guardado` (`python main.py --bench guardado`)

| Filas | Medición, para 10, 100 y 1 000 salas | Tipo | Carga |
|---|---|---|---|
| verificación | cargar devuelve el mismo estado; otra versión se rechaza | cuenta (ok/falla) | — |
| existentes | tamaño en disco (binario y JSON) | cuenta | cazador con `rango`, salidas con `costo`, conocimiento de la mitad de las salas |
| existentes | guardar completa (binario y JSON) | tiempo | igual |
| existentes | cargar completa (binario → DTO y JSON) | tiempo | igual |
| existentes | cargar UNA sala, la del medio (binario) y conseguirla en JSON | tiempo | igual |
| **nuevas** (desde M1) | bytes leídos al cargar UNA sala: primera, del medio y última | cuenta | igual |
| **nuevas** (desde M1) | tiempo de cargar UNA sala: primera y última (binario) | tiempo | igual |

## Formato de `mediciones.md`

1. **Encabezado de cada ejecución**: id (M0, M1, M2 o M2'), fecha y hora, commit (`git rev-parse --short HEAD`, más «árbol con cambios» si corresponde), comandos exactos, código de salida y la salida de consola entre bloques de código.
2. **Tabla por bloque**:

   `| # | Sección | Medición | Tipo | Antes (M0) | Carga (M1) | Después (M2) | Diferencia | Límite (2×) | Cumple | Causa |`

3. **Comprobación de las filas de cuenta**: M2 = M2' fila por fila (FR-379) y M1 = M2 en las secciones 1 y 6 del bloque `cache` (FR-387).
4. **Medición manual**: la cripta usada (o «ninguna publicada completa»), el tamaño del archivo, los bytes leídos por sala, el tiempo de una sala y de la carga completa, y 0 solicitudes.
5. **Pruebas**: el resultado de la suite completa en M0 y en M2, y el de `test_vecindad_equivalencia` y `test_cache_equivalencia` contra `0b031ec` y contra el código revisado.

Las tablas finales de antes y después y los veredictos se copian en la sección 012 de `DECISIONES.md` (FR-388).
