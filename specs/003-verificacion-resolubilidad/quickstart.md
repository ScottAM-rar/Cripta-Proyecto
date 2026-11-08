# Guía de validación: Verificación de resolubilidad

No necesita red salvo el paso 3, que es opcional y usa una cripta ya guardada (0 solicitudes si su caché está vigente). Los nombres de prueba de la matriz son los **previstos**; `/speckit-implement` los reemplaza por los nombres reales (`archivo: Clase.método`) al cerrar, como en la 009.

## 1. Pruebas de la capacidad

```text
python -m unittest test_mapa_con_llaves test_indice_llaves test_resolubilidad_regla test_resolubilidad_apendice_b test_resolubilidad_determinismo test_resolubilidad_datos test_resolubilidad_inicio test_resolubilidad_reporte
python -m unittest discover -p "test_*.py"      # la suite de la Parte I, 001, 005 y 009 sigue pasando
python -m tests_labs.sin_red                    # las pruebas de la capacidad con requests.get bloqueado
```

Resultado esperado: todo en verde; los cuatro casos B-R pasan.

## 2. Mediciones

```text
python main.py --bench resolubilidad
```

Con la máquina libre. Resultado esperado ([contracts/bench-resolubilidad.md](contracts/bench-resolubilidad.md)): A con resultados iguales en las dos estrategias; C por debajo de 200 ms; D con la razón de la incremental ≤ 20 y la de la repetida cerca de 100. Se copian a `mediciones.md` con la cabecera del bench (Python, sistema, fecha, semilla).

## 3. Cripta publicada más grande (opcional, FR-345)

1. Con la cripta más grande del catálogo ya guardada en `datos_cripta/` (jugada o descargada antes con red), crear una `FuenteSoloLocal` con `crear_fuente_solo_local` (009).
2. Cronometrar `verificar(fuente, <id>)` con `time.perf_counter_ns`, mediana de 5.
3. Anotar en `mediciones.md` el id, la cantidad de salas y el tiempo. Debe ser menor que 200 ms. El contador de solicitudes queda en 0.

## 4. Comprobación manual con la interfaz provisional (para Fernanda)

Después del primer grupo de tareas, desde un intérprete:

```text
servicio.verificar("cripta-01").codigo_salida()   → 2 con el cuerpo provisional; 0 o 1 cuando esté el algoritmo
lineas_reporte(servicio.verificar("cripta-01"))   → el texto de contracts/reporte-verificacion.md
```

## 5. Revisión de los principios I y IV

```text
grep -rnE "import (heapq|bisect|collections|networkx)|from (heapq|bisect|collections|networkx)|sorted\(|\.sort\(" Logica/VerificacionResolubilidad.py Logica/IndiceLlaves.py Logica/ReporteVerificacion.py DTO/ResultadoVerificacionDTO.py bench/resolubilidad.py
grep -rnE "^(from|import) (adaptadores|Controlador|Servicio)" Logica/VerificacionResolubilidad.py Logica/IndiceLlaves.py Logica/ReporteVerificacion.py
```

Ninguno debe encontrar nada. Revisar a mano que no haya `dict()`/`{}` ni `set()` usados como índice en esos archivos.

## Matriz de trazabilidad

### Requisitos funcionales

| Requisito | Escenario | Prueba o medición (prevista) |
|---|---|---|
| FR-330 | H1-1 | `test_resolubilidad_reporte`: `VerificarSinPartida.test_fr330_verificar_no_inicia_partida_ni_crea_log_ni_vista` |
| FR-331 | H1-1, H1-2, H5-1 | `test_resolubilidad_reporte`: `CodigosDeSalida.test_fr331_resoluble_0_no_resoluble_1_error_2` |
| FR-332 | H1-2, H1-4, H1-5 | `test_resolubilidad_regla`: `Regla.test_fr332_salida_alcanzable_y_llave_obtenible_es_resoluble`, `Regla.test_fr332_sala_inicial_es_salida`, `Regla.test_fr332_no_exige_puerta_hacia_la_salida`; `Bloqueos.test_fr332_fr338_salida_sin_camino`, `Bloqueos.test_fr332_fr338_llave_salida_inexistente` |
| FR-333 | H1-3, H1-6 | `test_resolubilidad_regla`: `Regla.test_fr333_cadena_de_puertas`, `Regla.test_fr333_respeta_salidas_de_un_solo_sentido`, `Regla.test_fr333_puerta_sin_llave_nunca_se_cruza`, `Regla.test_fr333_una_llave_abre_varias_puertas` |
| FR-334 | H2-1, H2-2, H2-3, H1-6 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r2_fr334_llave_de_errante_en_su_sala_inicial`; `test_resolubilidad_regla`: `Regla.test_fr334_enemigo_tras_puerta`, `Regla.test_fr334_basta_una_ubicacion_alcanzable` |
| FR-335 | H3-1, H3-2, H3-3, H3-4 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r3_fr335_dos_ejecuciones_mismo_orden`; `test_resolubilidad_determinismo`: `Determinismo.test_fr335_desempate_sala_y_luego_id` (escenario H3-2: `A`, `B`, `X`), `Determinismo.test_fr335_orden_de_la_respuesta_no_importa`, `Determinismo.test_fr335_con_y_sin_contenido_guardado`, `Equivalencia.test_fr335_incremental_igual_a_repetida_en_criptas_al_azar` |
| FR-336 | H1-1, H1-3, H2-1 | `test_resolubilidad_reporte`: `Texto.test_fr336_resoluble_muestra_orden_con_sala_y_enemigo`; `test_resolubilidad_regla`: `Regla.test_fr336_llave_salida_en_el_orden_una_vez` |
| FR-337 | H1-2, H1-4 | `test_resolubilidad_regla`: `Bloqueos.test_fr337_salas_alcanzables_crecientes_y_cantidad_no_alcanzables`; `test_resolubilidad_reporte`: `Texto.test_fr337_lista_salas_alcanzables` |
| FR-338 | H1-2, H1-4, H1-5 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r1_fr338_ciclo`, `CasosB.test_b_r4_fr338_llave_inexistente`; `test_resolubilidad_regla`: `Bloqueos.test_fr338_varios_bloqueos_en_orden`, `Bloqueos.test_fr338_tipos_sin_llave_y_sin_camino` |
| FR-339 | H4-1, H4-3, H4-4 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r4_fr339_no_inicia_sin_forzar`; `test_resolubilidad_inicio`: `Inicio.test_fr339_no_resoluble_no_inicia_y_no_crea_log`, `Inicio.test_fr339_resoluble_inicia_sin_aviso`, `Inicio.test_fr339_fr313_sin_llaves_sigue_con_aviso`, `Inicio.test_fr339_replay_y_partida_cargada_no_verifican` |
| FR-340 | H4-2, H4-3 | `test_resolubilidad_inicio`: `Forzar.test_fr340_forzar_inicia_con_aviso_solo_al_iniciar`, `Forzar.test_fr340_forzar_sin_efecto_en_resoluble` |
| FR-341 | H3-3, H5-3 | `test_resolubilidad_datos`: `Solicitudes.test_fr341_llaves_guardadas_cero_solicitudes`, `Solicitudes.test_fr341_sin_llaves_solo_la_consulta_de_la_009`, `Solicitudes.test_fr341_nunca_pide_contenido`, `Solicitudes.test_fr341_inicio_reutiliza_las_llaves_de_la_partida` |
| FR-342 | H3-4, H5-2 | `test_resolubilidad_determinismo`: `Fuentes.test_fr342_http_offline_y_solo_local_dan_lo_mismo`; `test_mapa_con_llaves` (G3, G4) |
| FR-343 | H5-1, H5-2, H5-4 | `test_resolubilidad_datos`: `ErroresDeDatos.test_fr343_servicio_sin_respuesta`, `ErroresDeDatos.test_fr343_offline_sin_llaves_sin_solicitudes`, `ErroresDeDatos.test_fr343_cripta_inexistente`, `ErroresDeDatos.test_fr343_sala_de_salida_inexistente` |
| FR-344 | H3-5 | `test_resolubilidad_inicio`: `MismaOperacion.test_fr344_inicio_y_verificar_dan_el_mismo_resultado`; `test_resolubilidad_reporte`: `Contrato.test_fr344_firmas_de_la_interfaz` |
| FR-345 | H6-1 | `--bench resolubilidad` sección C; paso 3 de esta guía; ambos en `mediciones.md` |
| FR-346 | H6-2 | `--bench resolubilidad` secciones A y D; `test_resolubilidad_determinismo`: `Equivalencia` (las dos estrategias coinciden) |

### Casos del Apéndice B

| Caso | Requisitos | Prueba |
|---|---|---|
| B-R1 | FR-332, FR-333, FR-334, FR-337, FR-338 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r1_fr338_ciclo` |
| B-R2 | FR-334, FR-336 | `CasosB.test_b_r2_fr334_llave_de_errante_en_su_sala_inicial` |
| B-R3 | FR-335, FR-336 | `CasosB.test_b_r3_fr335_dos_ejecuciones_mismo_orden` |
| B-R4 | FR-338, FR-339 | `CasosB.test_b_r4_fr339_no_inicia_sin_forzar`, `CasosB.test_b_r4_fr338_llave_inexistente` |

### Criterios de éxito

| Criterio | Cómo se comprueba |
|---|---|
| SC-001 | `test_resolubilidad_apendice_b` en verde |
| SC-002 | `test_resolubilidad_determinismo` (`Determinismo`) |
| SC-003 | `test_resolubilidad_datos` (`Solicitudes`) |
| SC-004 | `test_resolubilidad_datos` (`ErroresDeDatos`) y `CodigosDeSalida` |
| SC-005 | `test_resolubilidad_inicio` (`Inicio`, `Forzar`) |
| SC-006 | Paso 3 de esta guía y sección C del bench |
| SC-007 | Sección D del bench |

### Cambio de contrato del mapa (no es un FR de la spec; habilita FR-333)

| Garantía | Prueba |
|---|---|
| G1 a G6 de [contracts/mapa-con-llaves.md](contracts/mapa-con-llaves.md) | `test_mapa_con_llaves`: una prueba por garantía |
