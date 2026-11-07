# Contrato: consulta de llaves del servicio

## Solicitud

`GET /criptas/<id>/llaves`, con el encabezado `X-Cripta-Client-Id` igual que el resto. **Cuenta como una solicitud** en `solicitudes_realizadas`, y cada 429 reintentado también cuenta, como en las demás consultas.

## Respuesta 200 (forma confirmada con el Swagger, esquemas `LlavesResponse` y `KeyLocation`, 2026-11-06; research.md §1)

```json
{
  "llaves": [
    {"id": "itm_llave_bronce", "sala": 3},
    {"id": "itm_llave_negra", "sala": 4, "enemigo": "e-401"}
  ]
}
```

| Campo | Tipo | Obligatorio | Significado |
|---|---|---|---|
| `llaves` | lista | sí | Puede ser vacía |
| `llaves[i].id` | texto no vacío | sí | Id de catálogo de la llave |
| `llaves[i].sala` | entero | sí | Sala de la llave, o sala inicial del enemigo que la suelta |
| `llaves[i].enemigo` | texto o `null` | no | `instancia` del enemigo que suelta la llave |

## Lector (`adaptadores/llaves.py`)

```text
leer_llaves(respuesta_json: dict) -> list[dict]
    # Extrae respuesta["llaves"]. Lanza LlavesInvalidas si falta o no es una lista.
validar_llaves(crudas, existe: list[bool], contenido_guardado) -> (ids, salas, enemigos)
    # Reglas de FR-311 en el orden de research.md §5. Lanza LlavesInvalidas(motivo).
    # contenido_guardado(sala) -> dict | None ; nunca hace solicitudes.
```

El `dict` de la respuesta solo se lee aquí (principio I). A partir de aquí todo circula como listas paralelas.

## Casos de validación (cada uno con su prueba en `test_llaves_validacion.py`)

| Entrada | Resultado |
|---|---|
| `{"llaves": []}` | Válida, 0 llaves |
| Falta `llaves` o no es una lista | Inválida |
| Entrada sin `id` o sin `sala`, `sala` no entera o `id` vacío | Inválida |
| `sala` fuera del esqueleto | Inválida |
| Misma llave en las salas 3 y 9 | Válida, 2 ubicaciones |
| Misma llave en la misma sala con enemigos distintos | Válida |
| Dos entradas idénticas (`id`, `sala` y `enemigo`) | Inválida |
| `enemigo` presente, contenido de la sala guardado y el enemigo no está en él | Inválida |
| `enemigo` presente y contenido de la sala no guardado | Válida, sin solicitudes |
