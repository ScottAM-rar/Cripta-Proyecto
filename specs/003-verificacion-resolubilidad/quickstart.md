# Guía de validación: Verificación de resolubilidad

No necesita red. El paso 3 es opcional y lee una cripta ya guardada en `datos_cripta/` (0 solicitudes). Los nombres de prueba de la matriz son los **reales** (`archivo: Clase.método`), tomados de los archivos que existen al cerrar (T062).

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

Con la máquina libre. Resultado esperado ([contracts/bench-resolubilidad.md](contracts/bench-resolubilidad.md)): A con resultados iguales en las dos estrategias; C por debajo de 200 ms; D con la razón de la incremental ≤ 20. La razón de la repetida no es «cercana a 100» como se preveía: se midió **1 112,8**, porque el oráculo, además de recorrer desde cero en cada oleada, busca linealmente si una llave ya se obtuvo, y su costo se acerca a O(K² · (S + E)) ([mediciones.md](mediciones.md)). Se copian a `mediciones.md` con la cabecera del bench (Python, sistema, fecha, semilla).

## 3. Cripta publicada más grande (opcional, FR-345)

La verificación necesita el mapa, los datos generales y las llaves de la cripta, **no el contenido de las salas** (FR-341). Por eso la medición usa los datos guardados sin exigir la cripta completa:

1. Con el mapa, los datos generales y las llaves de la cripta más grande del catálogo guardados en `datos_cripta/` (por ejemplo, después de verificarla o jugarla una vez con red), armar en un guion temporal, fuera del repositorio, un `ServicioCripta` sobre un cliente que lea solo de disco: una subclase de `ClienteOffline` cuyo `obtener_criptas` devuelva la lista guardada tal cual (`almacen.leer_criptas()`), sin el filtro de cripta completa. Bloquear la red (`requests.get`).
2. Cronometrar con `time.perf_counter_ns`, mediana de 5: (a) `verificar(servicio, <id>)`, con un servicio nuevo en cada repetición (lectura de disco, armado del mapa y de las llaves y algoritmo), y (b) solo `verificar_resolubilidad(mapa, sala_inicial, sala_salida, llave_salida, llaves, <id>)` con el `MapaCripta` y la `UbicacionLlavesDTO` ya construidos.
3. Comprobar que los dos dan el mismo reporte (`lineas_reporte`), que `solicitudes_realizadas` queda en 0 y que los archivos de `datos_cripta/` no cambian (sha1 antes y después).
4. Anotar en `mediciones.md` el id, la cantidad de salas y de llaves, el resultado, los dos tiempos y las solicitudes. Debe ser menor que 200 ms.

Por qué no se usa `FuenteSoloLocal` ni `ClientePersistente`: `ClienteOffline` (y con él `crear_fuente_solo_local` y `--offline`) solo da por existente una cripta guardada **por completo**, con el contenido de todas sus salas. Descargar ese contenido solo para medir gastaría solicitudes que la verificación no usa. `ClientePersistente` pide a la red la lista de criptas y los datos generales al empezar la sesión (arranque de la Parte I). Así se hizo T057 (cripta-06, 300 salas: 2,925 ms y 0,391 ms, 0 solicitudes).

**Alternativa, si la cripta está completa en disco**: `crear_fuente_solo_local()` (009) y cronometrar `verificar(fuente, <id>)` del mismo modo. Es equivalente a jugar con `--offline`. En T057 dio el mismo reporte que el método de arriba en cripta-04 y cripta-05, las dos completas.

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

Las 83 pruebas de los 8 archivos de la capacidad aparecen en esta matriz. Las que se prueban en la operación y no desde la consola lo dicen: conectar `--verificar` y `--forzar` y mostrar el reporte y los avisos es de la capacidad que conecta esas opciones (Fernanda).

### Requisitos funcionales

| Requisito | Escenario | Prueba o medición |
|---|---|---|
| FR-330 | H1-1 | `test_resolubilidad_reporte`: `VerificarSinPartida.test_fr330_verificar_no_inicia_partida_ni_crea_log_ni_vista` (en la operación; la prueba desde la consola es de la capacidad que conecta `--verificar`) |
| FR-331 | H1-1, H1-2, H5-1 | `test_resolubilidad_reporte`: `Contrato.test_fr331_codigo_salida`, `CodigosDeSalida.test_fr331_resoluble_0_no_resoluble_1_error_2` (en la operación) |
| FR-332 | H1-1, H1-2, H1-4, H1-5 | `test_resolubilidad_regla`: `Regla.test_fr332_h1_1_salida_alcanzable_y_llave_obtenible_es_resoluble`, `Regla.test_fr332_sala_inicial_es_salida`, `Regla.test_fr332_no_exige_puerta_hacia_la_salida`, `Bloqueos.test_fr332_fr338_h1_4_salida_sin_camino`, `Bloqueos.test_fr332_fr338_h1_5_llave_salida_inexistente` |
| FR-333 | H1-3, H1-6 | `test_mapa_con_llaves`: `MapaConLlaves.test_fr333_g1_esqueleto_copia_la_llave`, `MapaConLlaves.test_fr333_g2_mapa_cripta_copia_la_llave`, `MapaConLlaves.test_g5_construccion_sin_llave_sigue_funcionando`; `test_resolubilidad_regla`: `Regla.test_fr333_h1_3_cadena_de_puertas`, `Regla.test_fr333_h1_6_respeta_salidas_de_un_solo_sentido`, `Regla.test_fr333_puerta_sin_llave_nunca_se_cruza`, `Regla.test_fr333_una_llave_abre_varias_puertas`; `test_resolubilidad_datos`: `CasosLimite.test_fr333_salida_a_sala_inexistente_se_ignora` |
| FR-334 | H2-1, H2-2, H2-3, H1-6 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r2_fr334_llave_de_errante_en_su_sala_inicial`; `test_resolubilidad_regla`: `Regla.test_fr334_h2_2_enemigo_tras_puerta`, `Regla.test_fr334_h2_3_basta_una_ubicacion_alcanzable`, `Regla.test_fr333_h1_6_respeta_salidas_de_un_solo_sentido` |
| FR-335 | H3-1, H3-2, H3-3 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r3_fr335_dos_ejecuciones_mismo_orden`; `test_resolubilidad_determinismo`: `Determinismo.test_fr335_h3_2_dos_oleadas` (H3-2: sala inicial 5, orden `A`, `B`, `X`, `C`), `Determinismo.test_fr335_orden_de_la_respuesta_no_importa`, `Determinismo.test_fr335_suelo_antes_que_enemigo_y_menor_instancia`, `Determinismo.test_fr335_dos_ejecuciones_iguales`, `DeterminismoConContenido.test_fr335_h3_3_con_y_sin_contenido_guardado`, `Equivalencia.test_fr335_fr346_incremental_igual_a_repetida_en_criptas_al_azar`; `test_resolubilidad_reporte`: `Texto.test_fr335_mismo_resultado_mismo_reporte`; `test_indice_llaves`: `IndiceLlavesPrueba.test_fr335_ids_quedan_en_orden_creciente`, `IndiceLlavesPrueba.test_fr335_repetidos_cuentan_una_vez`, `IndiceLlavesPrueba.test_fr335_numero_de_un_id_presente`, `IndiceLlavesPrueba.test_fr335_numero_de_un_id_ausente_es_menos_uno`, `IndiceLlavesPrueba.test_lista_vacia`, `IndiceLlavesPrueba.test_un_solo_elemento`, `IndiceLlavesPrueba.test_prefijos_compartidos`, `IndiceLlavesPrueba.test_fr335_igual_que_busqueda_lineal` |
| FR-336 | H1-1, H1-3, H2-1 | `test_resolubilidad_reporte`: `Texto.test_fr336_resoluble_muestra_orden_con_sala_y_enemigo`; `test_resolubilidad_regla`: `Regla.test_fr336_llave_salida_en_el_orden_una_vez` |
| FR-337 | H1-2, H1-4 | `test_resolubilidad_regla`: `Bloqueos.test_fr337_salas_alcanzables_crecientes_y_cantidad_no_alcanzables`; `test_resolubilidad_reporte`: `Texto.test_fr337_lista_salas_alcanzables` |
| FR-338 | H1-2, H1-4, H1-5, H1-7 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r1_fr338_ciclo`, `CasosB.test_b_r4_fr338_llave_inexistente`; `test_resolubilidad_regla`: `Bloqueos.test_fr338_varios_bloqueos_en_orden`, `Bloqueos.test_fr338_puerta_sin_llave_es_bloqueo_sin_llave`, `Bloqueos.test_fr338_h1_7_llave_en_sala_sin_camino_es_bloqueo_no_ciclo`, `Bloqueos.test_fr338_ciclo_a_traves_de_otras_puertas`; `test_resolubilidad_reporte`: `Texto.test_fr338_texto_por_tipo_de_bloqueo`, `Texto.test_fr338_texto_por_causa`, `Texto.test_fr338_b_r1_reporte_completo` |
| FR-339 | H4-1, H4-3, H4-4, H4-5 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r4_fr339_no_inicia_sin_forzar`; `test_resolubilidad_inicio`: `Inicio.test_fr339_no_resoluble_no_inicia_y_no_crea_log`, `Inicio.test_fr339_resoluble_inicia_sin_aviso`, `Inicio.test_fr339_fr313_sin_llaves_sigue_con_aviso`, `Inicio.test_fr339_h4_5_datos_invalidos_inicia_con_aviso`, `Inicio.test_fr339_replay_y_partida_cargada_no_verifican`, `Inicio.test_fr339_reintento_tras_no_resoluble`, `Inicio.test_fr339_cambio_de_version_la_partida_nueva_no_inicia_sin_forzar`; `test_resolubilidad_reporte`: `Contrato.test_fr339_cripta_no_resoluble_es_runtime_error`; `test_resolubilidad_datos`: `CasosLimite.test_fr339_cambio_de_version_entre_verificar_y_la_partida` |
| FR-340 | H4-2, H4-3 | `test_resolubilidad_inicio`: `Forzar.test_fr340_forzar_inicia_con_aviso_solo_al_iniciar`, `Forzar.test_fr340_forzar_sin_efecto_en_resoluble`; `test_resolubilidad_reporte`: `AvisoForzado.test_fr340_aviso_forzado_una_linea` (en el modelo; mostrarlo es de la capacidad que conecta `--forzar`) |
| FR-341 | H3-3, H5-3 | `test_mapa_con_llaves`: `MapaConLlaves.test_fr341_g6_sin_solicitudes_nuevas`; `test_resolubilidad_datos`: `Solicitudes.test_fr341_llaves_guardadas_cero_solicitudes`, `Solicitudes.test_fr341_sin_llaves_solo_la_consulta_de_la_009`, `Solicitudes.test_fr341_nunca_pide_contenido`, `Solicitudes.test_fr341_inicio_reutiliza_las_llaves_de_la_partida`; `test_resolubilidad_determinismo`: `DeterminismoConContenido.test_fr335_h3_3_con_y_sin_contenido_guardado` |
| FR-342 | H3-4, H5-2 | `test_resolubilidad_determinismo`: `Fuentes.test_fr342_h3_4_http_offline_y_solo_local_dan_lo_mismo`; `test_mapa_con_llaves`: `MapaConLlaves.test_fr342_g3_offline_igual_que_con_red`, `MapaConLlaves.test_fr342_g4_fuente_solo_local_igual_sin_solicitudes`; `test_resolubilidad_datos`: `ErroresDeDatos.test_fr343_offline_sin_llaves_sin_solicitudes` |
| FR-343 | H4-5, H5-1, H5-2, H5-4 | `test_resolubilidad_datos`: `ErroresDeDatos.test_fr343_servicio_sin_respuesta`, `ErroresDeDatos.test_fr343_offline_sin_llaves_sin_solicitudes`, `ErroresDeDatos.test_fr343_cripta_inexistente`, `ErroresDeDatos.test_fr343_h4_5_sala_de_salida_inexistente`, `CasosLimite.test_fr343_ubicacion_de_llave_en_sala_inexistente_es_error_de_datos`; `test_resolubilidad_reporte`: `Contrato.test_fr343_sin_datos_devuelve_codigo_2` (reemplazó en T032 a la prueba del cuerpo provisional), `Texto.test_fr343_reporte_de_error` |
| FR-344 | H3-5 | `test_resolubilidad_inicio`: `MismaOperacion.test_fr344_inicio_y_verificar_dan_el_mismo_resultado`; `test_resolubilidad_reporte`: `Contrato.test_fr344_firmas_de_la_interfaz`, `Contrato.test_fr344_campos_del_resultado`, `Contrato.test_fr344_fuente_entrega_sala_inicial_y_llave_salida` |
| FR-345 | H6-1 | Evidencia automática: `--bench resolubilidad` sección C (cadena de 10 000 salas, 58,51 ms; rejilla de 4 900 salas, 16,00 ms; falla si supera 200 ms). Medición manual del paso 3 (T057): cripta-06, la publicada más grande (300 salas, 4 llaves), 2,925 ms con la verificación completa y 0,391 ms con la función pura, 0 solicitudes. Ambos en `mediciones.md` |
| FR-346 | H6-2 | `--bench resolubilidad` secciones A y D (razón 12,7 de la incremental frente a 1 112,8 de la repetida); `test_resolubilidad_determinismo`: `Equivalencia.test_fr335_fr346_incremental_igual_a_repetida_en_criptas_al_azar`, `CadenaSintetica.test_fr346_cadena_determinista_por_semilla`, `CadenaSintetica.test_fr346_cadena_es_resoluble_con_n_llaves`, `CadenaSintetica.test_fr346_ids_no_siguen_la_cadena` |

### Escenarios de aceptación

| Escenario | Prueba o medición |
|---|---|
| H1-1 | `test_resolubilidad_regla`: `Regla.test_fr332_h1_1_salida_alcanzable_y_llave_obtenible_es_resoluble`; `test_resolubilidad_reporte`: `Texto.test_fr336_resoluble_muestra_orden_con_sala_y_enemigo`, `CodigosDeSalida.test_fr331_resoluble_0_no_resoluble_1_error_2` (código 0), `VerificarSinPartida.test_fr330_verificar_no_inicia_partida_ni_crea_log_ni_vista` (en la operación) |
| H1-2 (B-R1) | `test_resolubilidad_apendice_b`: `CasosB.test_b_r1_fr338_ciclo`; `test_resolubilidad_reporte`: `Texto.test_fr338_b_r1_reporte_completo`, `CodigosDeSalida.test_fr331_resoluble_0_no_resoluble_1_error_2` (código distinto de cero) |
| H1-3 | `test_resolubilidad_regla`: `Regla.test_fr333_h1_3_cadena_de_puertas` |
| H1-4 | `test_resolubilidad_regla`: `Bloqueos.test_fr332_fr338_h1_4_salida_sin_camino` |
| H1-5 | `test_resolubilidad_regla`: `Bloqueos.test_fr332_fr338_h1_5_llave_salida_inexistente` |
| H1-6 | `test_resolubilidad_regla`: `Regla.test_fr333_h1_6_respeta_salidas_de_un_solo_sentido` |
| H1-7 | `test_resolubilidad_regla`: `Bloqueos.test_fr338_h1_7_llave_en_sala_sin_camino_es_bloqueo_no_ciclo` |
| H2-1 (B-R2) | `test_resolubilidad_apendice_b`: `CasosB.test_b_r2_fr334_llave_de_errante_en_su_sala_inicial` |
| H2-2 | `test_resolubilidad_regla`: `Regla.test_fr334_h2_2_enemigo_tras_puerta` |
| H2-3 | `test_resolubilidad_regla`: `Regla.test_fr334_h2_3_basta_una_ubicacion_alcanzable` |
| H3-1 (B-R3) | `test_resolubilidad_apendice_b`: `CasosB.test_b_r3_fr335_dos_ejecuciones_mismo_orden`; `test_resolubilidad_determinismo`: `Determinismo.test_fr335_dos_ejecuciones_iguales` |
| H3-2 | `test_resolubilidad_determinismo`: `Determinismo.test_fr335_h3_2_dos_oleadas` |
| H3-3 | `test_resolubilidad_determinismo`: `DeterminismoConContenido.test_fr335_h3_3_con_y_sin_contenido_guardado` |
| H3-4 | `test_resolubilidad_determinismo`: `Fuentes.test_fr342_h3_4_http_offline_y_solo_local_dan_lo_mismo`. La parte «con el cliente real» se prueba con el cliente HTTP falso: las pruebas no usan la red |
| H3-5 | `test_resolubilidad_inicio`: `MismaOperacion.test_fr344_inicio_y_verificar_dan_el_mismo_resultado` |
| H4-1 (B-R4) | `test_resolubilidad_apendice_b`: `CasosB.test_b_r4_fr339_no_inicia_sin_forzar`; `test_resolubilidad_inicio`: `Inicio.test_fr339_no_resoluble_no_inicia_y_no_crea_log` |
| H4-2 | `test_resolubilidad_inicio`: `Forzar.test_fr340_forzar_inicia_con_aviso_solo_al_iniciar` |
| H4-3 | `test_resolubilidad_inicio`: `Inicio.test_fr339_resoluble_inicia_sin_aviso`, `Forzar.test_fr340_forzar_sin_efecto_en_resoluble` |
| H4-4 | `test_resolubilidad_inicio`: `Inicio.test_fr339_fr313_sin_llaves_sigue_con_aviso` |
| H4-5 | `test_resolubilidad_inicio`: `Inicio.test_fr339_h4_5_datos_invalidos_inicia_con_aviso`; `test_resolubilidad_datos`: `ErroresDeDatos.test_fr343_h4_5_sala_de_salida_inexistente` (código 2) |
| H5-1 | `test_resolubilidad_datos`: `ErroresDeDatos.test_fr343_servicio_sin_respuesta` |
| H5-2 | `test_resolubilidad_datos`: `ErroresDeDatos.test_fr343_offline_sin_llaves_sin_solicitudes` |
| H5-3 | `test_resolubilidad_datos`: `Solicitudes.test_fr341_llaves_guardadas_cero_solicitudes`, `Solicitudes.test_fr341_nunca_pide_contenido` |
| H5-4 | `test_resolubilidad_datos`: `ErroresDeDatos.test_fr343_cripta_inexistente` |
| H6-1 | `--bench resolubilidad` sección C y medición manual de T057 (cripta-06: 2,925 ms), en `mediciones.md` |
| H6-2 | `--bench resolubilidad` secciones A y D, en `mediciones.md` |

### Casos del Apéndice B

| Caso | Requisitos | Prueba |
|---|---|---|
| B-R1 | FR-332, FR-333, FR-334, FR-337, FR-338 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r1_fr338_ciclo`; `test_resolubilidad_reporte`: `Texto.test_fr338_b_r1_reporte_completo` |
| B-R2 | FR-334, FR-336 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r2_fr334_llave_de_errante_en_su_sala_inicial` |
| B-R3 | FR-335, FR-336 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r3_fr335_dos_ejecuciones_mismo_orden` |
| B-R4 | FR-338, FR-339 | `test_resolubilidad_apendice_b`: `CasosB.test_b_r4_fr339_no_inicia_sin_forzar`, `CasosB.test_b_r4_fr338_llave_inexistente` |

### Criterios de éxito

| Criterio | Cómo se comprueba |
|---|---|
| SC-001 | `test_resolubilidad_apendice_b` en verde |
| SC-002 | `test_resolubilidad_determinismo` (`Determinismo` y `DeterminismoConContenido`) |
| SC-003 | `test_resolubilidad_datos` (`Solicitudes`) |
| SC-004 | `test_resolubilidad_datos` (`ErroresDeDatos`) y `test_resolubilidad_reporte` (`CodigosDeSalida`) |
| SC-005 | `test_resolubilidad_inicio` (`Inicio`, `Forzar`) |
| SC-006 | Sección C del bench (evidencia automática) y el paso 3 de esta guía (T057: cripta-06, 2,925 ms) |
| SC-007 | Sección D del bench (12,7 ≤ 20) |

### Cambio de contrato del mapa (no es un FR de la spec; habilita FR-333)

| Garantía de [contracts/mapa-con-llaves.md](contracts/mapa-con-llaves.md) | Prueba (`test_mapa_con_llaves`) |
|---|---|
| G1 | `MapaConLlaves.test_fr333_g1_esqueleto_copia_la_llave` |
| G2 | `MapaConLlaves.test_fr333_g2_mapa_cripta_copia_la_llave` |
| G3 | `MapaConLlaves.test_fr342_g3_offline_igual_que_con_red` |
| G4 | `MapaConLlaves.test_fr342_g4_fuente_solo_local_igual_sin_solicitudes` |
| G5 | `MapaConLlaves.test_g5_construccion_sin_llave_sigue_funcionando` |
| G6 | `MapaConLlaves.test_fr341_g6_sin_solicitudes_nuevas` |
