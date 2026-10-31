# Contrato de datos de entrada: esqueleto y catálogo

Lo que el programa acepta del servicio (y de la caché de disco / modo `--offline`, que lo entregan por la misma interfaz).

## Esqueleto de la cripta (`/salas`)

Cada salida admite un campo opcional `costo`:

```json
{ "id": 7, "nombre": "…", "salidas": { "N": { "sala": 8, "costo": 250 }, "E": { "sala": 3 } } }
```

| Situación | Resultado |
|---|---|
| `costo` ausente | 100 (FR-101) |
| `costo` entero ≥ 1 | Ese valor |
| `costo` cero, negativo, no entero o booleano | 100 y una advertencia que nombra la sala, la dirección y el valor |
| Costos distintos en las dos salidas de una misma conexión | **Pendiente de especificación** (ver `plan.md`). Regla provisional: vale el de la sala de menor id, con advertencia |

No se requieren solicitudes nuevas: el esqueleto ya se descarga completo al iniciar. Un esqueleto de la Parte I (sin `costo`) sigue siendo válido.

## Catálogo (`/catalogo`)

Ficha de enemigo cazador:

```json
{ "id": "…", "comportamiento": "cazador", "rango": 600, "velocidad": 100 }
```

| Situación | Resultado |
|---|---|
| `comportamiento == "cazador"` con `rango` entero ≥ 0 | Cazador con ese rango (FR-108) |
| `rango` ausente, negativo o no entero | Rango 0 y una advertencia |
| `rango == 0` | Válido: solo ataca en su sala |
| `comportamiento` no reconocido | Error actual de la Parte I |

## Validación de versiones

La caché de disco se valida con la versión de cripta y de catálogo que ya existe; no hay mecanismo nuevo y no se borran archivos a mano (FR-119).
