# Guía de validación: Contrato de datos v2 y ubicación de llaves

No necesita red. El paso 0 es opcional.

## 0. Forma de `/llaves` (confirmada con el Swagger; comprobación con red opcional, gasta 1 solicitud)

La forma ya se confirmó con el Swagger (`LlavesResponse` / `KeyLocation`, 2026-11-06). Si se quiere comprobar con el servicio real, hay que pedir `GET /criptas/cripta-01/llaves` y comparar la respuesta con [contracts/consulta-llaves.md](contracts/consulta-llaves.md). Si no coincide, se corrige `leer_llaves` y el contrato antes de seguir (research.md §1).

## 1. Pruebas de la capacidad

```text
python -m unittest test_llaves_validacion test_llaves_clientes test_llaves_presupuesto test_llaves_version test_llaves_fallos test_llaves_partida_cargada test_fuente_solo_local test_api_falsa_v2
python -m unittest discover -p "test_*.py"      # la suite de la Parte I, la 001 y la 005 sigue pasando
```

## 2. Mediciones

```text
python main.py --bench llaves
```

Resultado esperado: la sección D informa `1 / 0 / 0`; la B queda por debajo del límite; las secciones A y C muestran las dos alternativas. Los números y la recomendación se copian a `mediciones.md`.

## 3. Comprobación manual de los mensajes (offline)

1. Juega una cripta con red y luego quita la clave `llaves` del archivo de prueba con la ayuda de `tests_labs` (no a mano).
2. `python main.py --offline`: aparece el aviso «No se pudieron obtener las llaves de la cripta …», la partida se juega y el reporte final muestra 0 solicitudes.

## 4. Revisión del principio I

```text
grep -rnE "import (heapq|bisect|collections)|from collections" adaptadores/llaves.py adaptadores/fuente_solo_local.py DTO/LlavesDTO.py bench/llaves.py
```

No debe encontrar nada. El `deque` existente en `servicioCripta.py` es de la Parte I y no debe tener usos nuevos.

## Matriz de trazabilidad

| Requisito | Escenario | Prueba |
|---|---|---|
| FR-301 | H1-1, H1-4 | `test_llaves_presupuesto` (una sola llamada `("llaves", …)` por sesión) |
| FR-302 | H1-2, H1-3, H1-5 | `test_llaves_validacion`, `test_llaves_clientes` |
| FR-303 | H5-5 | `test_llaves_clientes` (misma lista con el HTTP simulado, el persistente y el offline) |
| FR-304 | H1-1 | `test_llaves_presupuesto` (contador y `reporte().texto()`) |
| FR-305, FR-306 | H2-1 | `test_llaves_version` |
| FR-307 | H2-2 | `test_llaves_version` |
| FR-308 | H2-3 | `test_llaves_version` (archivo de la Parte I sin clave `llaves`) |
| FR-309 | H3-1, casos límite (sin presupuesto) | `test_llaves_fallos` |
| FR-310 | H3-1, H3-2 | `test_llaves_fallos` (el archivo no tiene `llaves` después del fallo) |
| FR-311 | H3-2, H1-5 | `test_llaves_validacion` (tabla de contracts/consulta-llaves.md) |
| FR-312 | H3-3, H3-4 | `test_llaves_fallos`, `test_llaves_clientes` |
| FR-313 | H3-3, H2-6 | `test_llaves_fallos` (`iniciarJuego` sigue; `llaves is None`; `avisoLlaves` nombra la cripta). La regla de `--verificar` es de la capacidad 003 |
| FR-314, FR-316 | H4-2 | `test_fuente_solo_local` |
| FR-315 | H4-1 | `test_fuente_solo_local` (espía HTTP sin llamadas; el archivo no cambia) |
| FR-317 | H4-3 | `test_fuente_solo_local` |
| FR-318 | H5-1 | `test_api_falsa_v2` |
| FR-319 | H5-2 | `test_api_falsa_v2` (`cripta_v2`) |
| FR-320 | H5-3 | `test_api_falsa_v2` (un caso por código B-T, B-N, B-R y B-L de `CASOS_APENDICE_B`; 23 casos) |
| FR-321 | H5-4 | `test_api_falsa_v2` |
| FR-322, FR-323 | H6-1 | `--bench llaves`, sección A |
| FR-324 | H6-2 | `mediciones.md`; revisión de que `precargar_vecinas` no cambió |
| FR-325 | H2-4, H2-5, H2-6 | `test_llaves_partida_cargada` (0 solicitudes al cargar; guardadas → 0; faltan con presupuesto → 1; sin presupuesto → aviso; restaurar reinicia las llaves) |
| SC-001, SC-002 | — | `--bench llaves`, sección D |
| SC-004 | — | `test_llaves_presupuesto` (c), `test_llaves_fallos`, `test_fuente_solo_local` (los mensajes nombran la cripta) |
| SC-005 | — | `test_llaves_presupuesto` (con el presupuesto agotado no hay solicitud; con 1 restante, un 429 no se reintenta) |
| SC-006 | — | Las 8 pruebas nuevas con `requests.get` bloqueado (T051), dos veces con el mismo resultado |
| SC-007 | — | `--bench llaves`, sección A (lados 10, 20 y 40) |
