# Contrato: formato de la partida guardada

| Elemento | Antes | Ahora |
|---|---|---|
| `VERSION_ESTADO` (DTO) | 2 | **3** |
| `VERSION_FORMATO` (archivo binario) | 5 | **6** |
| Campos nuevos | — | `SalidaGuardadaDTO.costo` (entero); `EnemigoGuardadoDTO.rango` (entero) |

Reglas:

- Los campos nuevos se agregan **al final** de su DTO. El orden de `CLASES_DTO` no cambia.
- Un archivo de versión anterior se **rechaza** con un mensaje que indica la versión encontrada y la esperada. No se carga en silencio ni se migra (principio VI): no contiene costos ni cazadores y continuarlo no sería seguro.
- El cazador no guarda estado propio ni estado aleatorio. Su decisión se calcula del mundo restaurado, así que una partida restaurada y la original producen las mismas decisiones.
- Los logs de partida de la Parte I siguen reproduciéndose: el costo de cada acción del jugador se lee del log; los movimientos de enemigos se recalculan con las reglas vigentes y el log valida la versión de la cripta.
