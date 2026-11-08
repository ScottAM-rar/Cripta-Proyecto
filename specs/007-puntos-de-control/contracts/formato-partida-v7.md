# Contrato de Formato Binario de Partida v7

**Archivo**: `contracts/formato-partida-v7.md` | **Fecha**: 2026-11-07 | **Especificación**: [spec.md](../spec.md)

Este documento especifica formalmente los cambios en el formato binario de persistencia de partidas para quien mantiene `adaptadores/AlmacenPartidaBinario.py` y `DTO/EstadoGuardadoDTO.py`.

---

## 1. Identificación y Cabecera

El archivo binario de partida mantiene la firma mágica y avanza el número de versión:

```text
Offset  Tamaño  Tipo        Contenido       Descripción
0x00    4       bytes       b"CRPP"         Magia de identificación del formato
0x04    2       uint16 (BE) 7               VERSION_FORMATO (anteriormente 6)
```

Cualquier archivo cuya magia difiera de `b"CRPP"` o cuya versión no sea exactamente `7` DEBE ser rechazado inmediatamente con `ErrorPartida` (FR-425).

---

## 2. Nuevos Campos en la Estructura de Partida

Para incorporar los puntos de control y su configuración dentro del mismo archivo de guardado, se agregan las siguientes secciones/campos:

### 2.1. `k_checkpoint` (Intervalo vigente)
- **Nombre de sección**: `"k_checkpoint"`
- **Tipo**: Entero natural (codificado con `escribir_natural` / `leer_natural` del codec).
- **Semántica**: El valor de $K$ ($K \ge 1$) configurado para la partida. Si al cargar la partida el usuario invoca con `--checkpoint-cada K_nuevo`, el nuevo valor rige a partir de ese momento; de lo contrario, se mantiene este valor guardado.

### 2.2. `acciones_linea_tiempo` (Contador temporal vigente)
- **Nombre de sección**: `"acciones_linea_tiempo"`
- **Tipo**: Entero natural.
- **Semántica**: Acciones del jugador aceptadas y ejecutadas en la línea temporal activa (disminuido al usar el pergamino). Coincide con las acciones acumuladas en el estado actual.

### 2.3. `puntos_control` (Tabla de puntos de control)
- **Nombre de sección**: `"puntos_control"`
- **Estructura serializada**:
  ```text
  [cantidad_puntos: natural]
    Por cada punto de 0 a cantidad_puntos - 1:
      [acciones_linea_tiempo: natural]
      [tamano_bloque_estado: natural]
      [estado_serializado: bytes de tamaño tamano_bloque_estado]
  ```
  - `cantidad_puntos`: Total de puntos de control contenidos ($\ge 1$, incluye el punto 0 inicial).
  - Por cada punto de control:
    - `acciones_linea_tiempo`: El número de acciones de la línea de tiempo en el momento en que se tomó el punto ($0$ para el inicial, $n \times K$ para los periódicos).
    - `tamano_bloque_estado`: Longitud en bytes del bloque serializado del estado.
    - `estado_serializado`: Instantánea completa del estado correspondiente a `EstadoGuardadoDTO` (reutilizando el codec estándar de bloques de `EstadoGuardadoDTO` con su propio `VERSION_ESTADO = 3`).

---

## 3. Disposición General del Archivo v7

El formato conserva la arquitectura de secciones indexadas y tabla de salas al pie:

```text
+-----------------------------------------------------------+
| ENCABEZADO (6 bytes): b"CRPP" + uint16(7)                 |
+-----------------------------------------------------------+
| BLOQUES DE ESTADO ACTUAL:                                 |
|   - id_cripta, version_cripta, version_catalogo           |
|   - semilla, estado_azar, puntaje, acciones_jugador       |
|   - k_checkpoint (NUEVO)                                  |
|   - acciones_linea_tiempo (NUEVO)                         |
|   - jugador, reloj, bitacora, acciones_log                |
|   - enemigos, trampas, catalogos                          |
|   - puntos_control (NUEVO BLOQUE CONTENEDOR)              |
+-----------------------------------------------------------+
| BLOQUES DE SALAS (sala por sala, orden creciente de id)   |
+-----------------------------------------------------------+
| ÍNDICE DE SECCIONES:                                      |
|   - cantidad de secciones                                 |
|   - lista de (nombre, posicion, largo, crc32)             |
+-----------------------------------------------------------+
| TABLA DE SALAS:                                           |
|   - lista de entradas fijas (id, pos, largo, crc32)       |
+-----------------------------------------------------------+
| PIE DE ARCHIVO (28 bytes):                                |
|   - pos_secciones (uint64)                                |
|   - largo_secciones (uint32)                              |
|   - pos_tabla_salas (uint64)                              |
|   - cantidad_salas (uint32)                               |
|   - b"FIN!" (4 bytes)                                     |
+-----------------------------------------------------------+
```

---

## 4. Política de Compatibilidad y Migración (FR-425)

1. **Rechazo estricto de versiones anteriores**:
   - Si `version < 7` (versiones 1 a 6 de la Parte I o capacidades iniciales de Parte II):
     ```python
     raise ErrorPartida(
         f"Versión del formato de partida no soportada: {version} "
         f"(este programa usa la versión 7 con puntos de control)"
     )
     ```
2. **Justificación del rechazo frente a la migración automática**:
   - En v6 no existía almacenamiento periódico de puntos de control ni registro retroactivo de deltas pasados más allá de los 5 del pergamino.
   - Fabricar un archivo v7 sin puntos de control intermedios (o solo con el punto final) generaría archivos semánticamente incompletos que fallarían al intentar usar comandos de retroceso temporal o historia.
   - No se realiza migración silenciosa para garantizar el cumplimiento estricto del **Principio VI** de la Constitución y el **Apéndice B** del enunciado: *"Se carga un archivo de partida de la primera parte: se detecta como incompatible o se migra de forma explícita; nunca se carga en silencio"*.
