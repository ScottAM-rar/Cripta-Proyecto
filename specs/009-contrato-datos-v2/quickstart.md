# Guía de validación: Contrato de datos v2 y ubicación de llaves

No necesita red. El paso 0 es opcional.

## 0. Forma de `/llaves` (confirmada con el Swagger; comprobación con red opcional, gasta 1 solicitud)

La forma ya se confirmó con el Swagger (`LlavesResponse` / `KeyLocation`, 2026-11-06). Si se quiere comprobar con el servicio real, hay que pedir `GET /criptas/cripta-01/llaves` y comparar la respuesta con [contracts/consulta-llaves.md](contracts/consulta-llaves.md). Si no coincide, se corrige `leer_llaves` y el contrato antes de seguir (research.md §1).

## 1. Pruebas de la capacidad

```text
python -m unittest test_llaves_validacion test_llaves_dto test_llaves_clientes test_llaves_presupuesto test_llaves_version test_llaves_fallos test_llaves_partida_cargada test_fuente_solo_local test_api_falsa_v2
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

Nombres reales de las pruebas (`archivo: Clase.método`), tomados de los archivos que existen hoy (T038). Todas corren
sin red; las 9 pruebas de la capacidad también corren con `requests.get` bloqueado con `python -m tests_labs.sin_red`
(T051). Las mediciones salen de `python main.py --bench llaves` (`bench/llaves.py`) y están en
[mediciones.md](mediciones.md).

### Requisitos funcionales

| Requisito | Escenario | Prueba o medición |
|---|---|---|
| FR-301 | H1-1, H1-4, H2-5 | `test_llaves_presupuesto`: `PrimeraPartida.test_fr301_fr304_a_h1_1_primera_partida_hace_una_consulta_de_llaves_ademas_de_la_linea_base`, `UnaVezPorSesion.test_fr301_b_h1_4_dos_consultas_en_la_misma_sesion_hacen_una_sola_solicitud`, `PresupuestoAgotado.test_fr301_d_sin_presupuesto_con_llaves_guardadas_las_devuelve_sin_solicitudes`; `test_llaves_version`: `VersionCambiaDuranteLaPartida.test_fr301_fr307_e_cambio_de_version_en_la_sesion_no_consulta_y_la_siguiente_invalida`; `test_llaves_partida_cargada`: `SinLlavesGuardadas.test_fr325_c_h2_5_sin_llaves_guardadas_la_primera_pide_una_vez_y_la_segunda_ninguna` |
| FR-302 | H1-2, H1-3, H1-5 | `test_llaves_clientes`: `UbicacionLlavesDelServicio.test_fr302_b_h1_2_llave_soltada_por_enemigo_trae_su_sala_inicial`, `UbicacionLlavesDelServicio.test_fr302_c_h1_3_llave_en_el_suelo_no_tiene_enemigo`, `UbicacionLlavesDelServicio.test_fr302_d_h1_5_misma_llave_en_dos_salas_da_dos_ubicaciones`; `test_llaves_validacion`: `CasosDeValidacion.test_fr302_fila5_misma_llave_en_salas_3_y_9_es_valida_con_2_ubicaciones`, `CasosDeValidacion.test_fr302_fila6_misma_llave_misma_sala_enemigos_distintos_es_valida`, `EnemigoConContenidoGuardado.test_fr302_enemigo_que_esta_en_el_contenido_guardado_es_valido`, `LeerLlaves.test_fr302_devuelve_la_lista_tal_cual`, `LeerLlaves.test_fr302_llaves_vacia_devuelve_lista_vacia`, `OrdenDeLaRespuesta.test_fr302_se_conserva_el_orden_de_la_respuesta`, `OrdenDeLaRespuesta.test_fr302_mismo_resultado_en_dos_ejecuciones`; `test_llaves_dto`: `UbicacionLlaves.test_fr302_a_…` a `UbicacionLlaves.test_fr302_e_…` (5 pruebas, T052) |
| FR-303 | H5-5 | `test_llaves_clientes`: `MismaListaPorLosTresClientes.test_fr303_e_h5_5_http_persistente_y_offline_dan_la_misma_lista` |
| FR-304 | H1-1 | `test_llaves_presupuesto`: `PrimeraPartida.test_fr301_fr304_a_h1_1_primera_partida_hace_una_consulta_de_llaves_ademas_de_la_linea_base` (contador y `reporte().texto()`); `test_llaves_clientes`: `ClienteHttpObtenerLlaves.test_fr304_a_http_pide_la_ruta_de_llaves_con_el_encabezado_y_cuenta_una_solicitud`, `ClienteHttpObtenerLlaves.test_fr304_a_http_con_solo_guardadas_no_hace_la_solicitud` |
| FR-305 | H2-1 | `test_llaves_version`: `MismaVersion.test_fr306_a_h2_1_segunda_ejecucion_con_la_misma_version_no_consulta`, `OtraVersion.test_fr307_b_h2_2_con_otra_version_consulta_una_vez_y_guarda_la_lista_nueva` (la lista queda en disco con la versión); laboratorio `python -m tests_labs.prueba_almacen_disco`, sección «Llaves» (T007) |
| FR-306 | H2-1, H2-2 | `test_llaves_version`: `MismaVersion.test_fr306_a_h2_1_segunda_ejecucion_con_la_misma_version_no_consulta`, `ReutilizadaIgualQueDesdeCero.test_principio_iii_d_reutilizada_de_disco_y_memorizada_igual_a_consulta_desde_cero` |
| FR-307 | H2-2, H2-3 | `test_llaves_version`: `OtraVersion.test_fr307_b_h2_2_con_otra_version_consulta_una_vez_y_guarda_la_lista_nueva`, `VersionCambiaDuranteLaPartida.test_fr301_fr307_e_cambio_de_version_en_la_sesion_no_consulta_y_la_siguiente_invalida` |
| FR-308 | H2-3 | `test_llaves_version`: `ArchivoDeLaParteI.test_fr308_c_h2_3_archivo_sin_llaves_se_consulta_una_vez_y_queda_con_llaves` |
| FR-309 | H3-1, H3-2, casos límite (sin presupuesto) | `test_llaves_fallos`: `SinRespuesta.test_fr309_fr310_a_h3_1_sin_respuesta_avisa_con_la_cripta_y_no_guarda`, `FalloNoMemorizado.test_fr309_e_tras_un_fallo_la_segunda_llamada_vuelve_a_intentar`; `test_llaves_presupuesto`: `PresupuestoAgotado.test_fr309_c_sc005_sin_presupuesto_ni_llaves_guardadas_no_consulta_y_avisa_con_la_cripta` |
| FR-310 | H3-1, H3-2 | `test_llaves_fallos`: `SinRespuesta.test_fr309_fr310_a_h3_1_sin_respuesta_avisa_con_la_cripta_y_no_guarda`, `RespuestaInvalida.test_fr310_fr311_b_h3_2_respuestas_invalidas_avisan_y_no_guardan_nada`, `TemporalSobrante.test_fr310_f_un_tmp_sobrante_se_ignora_y_las_llaves_se_guardan` |
| FR-311 | H3-2, H1-5 | `test_llaves_validacion`: `CasosDeValidacion.test_fr311_fila1_…`, `fila2_…`, `fila3_…`, `fila4_…`, `fila7_…`, `fila8_…`, `fila9_…`, `LeerLlaves.test_fr311_respuesta_sin_llaves_es_invalida`, `LeerLlaves.test_fr311_llaves_que_no_es_lista_es_invalida`; `test_llaves_fallos`: `RespuestaInvalida.test_fr310_fr311_b_h3_2_respuestas_invalidas_avisan_y_no_guardan_nada` |
| FR-312 | H3-3, H3-4 | `test_llaves_fallos`: `ModoSinRed.test_fr312_fr313_c_h3_3_offline_sin_llaves_la_partida_sigue_con_aviso`, `ModoSinRed.test_fr312_d_h3_4_offline_con_llaves_las_entrega_sin_solicitudes` |
| FR-313 | H3-3, H2-6 | `test_llaves_fallos`: `ModoSinRed.test_fr312_fr313_c_h3_3_offline_sin_llaves_la_partida_sigue_con_aviso`, `FalloNoMemorizado.test_fr313_e_la_logica_tampoco_memoriza_el_fallo`, `AvisoEnElServicio.test_fr313_g_aviso_llaves_none_antes_de_iniciar_y_con_la_cripta_si_faltan`, `AvisoEnElServicio.test_fr313_g_aviso_llaves_none_si_hay_llaves`; `test_llaves_partida_cargada`: `SinLlavesYSinPoderPedirlas.test_fr313_fr325_d_h2_6_sin_presupuesto_no_pide_y_avisa`, `SinLlavesYSinPoderPedirlas.test_fr313_fr325_d_h2_6_sin_respuesta_avisa_y_la_partida_sigue`. La regla de `--verificar` es de la capacidad 003 |
| FR-314 | H4-1, H4-2 | `test_fuente_solo_local`: `IgualQueLaViaNormal.test_fr314_fr316_b_h4_2_con_la_cache_completa_da_lo_mismo_que_la_via_normal`, `ExisteCripta.test_fr314_t053_a_existe_cripta_con_lista_guardada_true_o_false_sin_comparar_version`, `ObjetosQueSuelta.test_fr314_t053_c_tras_consultar_la_cripta_da_lo_mismo_que_la_via_normal`, `SalidaYMapa.test_fr314_t053_d_sala_de_salida_y_mapa_iguales_a_la_via_normal`; laboratorio `python -m tests_labs.prueba_fabrica`, secciones 6 y 7 (T025, T053) |
| FR-315 | H4-1, H4-3 | `test_fuente_solo_local`: `DatoFaltante.test_fr315_a_h4_1_sin_contenido_de_la_sala_5_falla_nombrando_sala_y_cripta`, `ExisteCripta.test_fr315_t053_a_existe_cripta_sin_lista_en_disco_lanza`, `VersionCatalogo.test_fr315_t053_b_sin_version_de_catalogo_guardada_lanza`, `ObjetosQueSuelta.test_fr315_t053_c_ficha_ausente_lanza_con_el_id_de_la_ficha`, `ObjetosQueSuelta.test_fr315_t053_c_sin_ninguna_cripta_consultada_lanza` (todas comprueban además que el espía HTTP no recibe llamadas y que la carpeta queda igual byte a byte) |
| FR-316 | H4-2 | `test_fuente_solo_local`: `IgualQueLaViaNormal.test_fr314_fr316_b_h4_2_con_la_cache_completa_da_lo_mismo_que_la_via_normal`, `SinPrecarga.test_fr316_e_precargar_vecinas_devuelve_0_y_reporte_0_solicitudes` |
| FR-317 | H4-3 | `test_fuente_solo_local`: `VersionDistinta.test_fr317_c_h4_3_con_otra_version_vigente_toda_operacion_falla_nombrando_las_dos`, `VersionDistinta.test_fr317_c_sin_version_guardada_falla_aunque_no_se_pida_una`, `VersionCatalogo.test_fr317_t053_b_version_catalogo_distinta_lanza_nombrando_las_dos`, `VersionCatalogo.test_fr317_t053_b_version_catalogo_igual_o_none_devuelve_la_guardada`, `ObjetosQueSuelta.test_fr317_t053_c_ultima_cripta_con_otra_version_lanza`, `SalidaYMapa.test_fr317_t053_d_con_otra_version_lanzan` |
| FR-318 | H5-1 | `test_api_falsa_v2`: `Determinismo.test_fr318_a_h5_1_misma_semilla_mismas_respuestas_y_otra_semilla_cambia`, `CasosApendiceB.test_fr318_c_dos_construcciones_del_mismo_caso_dan_respuestas_identicas`, `SinRed.test_fr318_e_requests_get_esta_bloqueado_en_todo_el_archivo` |
| FR-319 | H5-2 | `test_api_falsa_v2`: `ContenidoDeCriptaV2.test_fr319_b_h5_2_hay_una_salida_con_costo_distinto_de_100`, `ContenidoDeCriptaV2.test_fr319_b_h5_2_hay_un_cazador_con_rango`, `ContenidoDeCriptaV2.test_fr319_b_h5_2_llave_sin_enemigo_con_enemigo_y_la_misma_en_dos_salas`, `ContenidoDeCriptaV2.test_fr319_b_h5_2_la_llave_de_salida_la_suelta_el_cazador`, `ContenidoDeCriptaV2.test_fr319_b_las_llaves_en_el_suelo_estan_en_el_contenido_y_tienen_ficha`, `ContenidoDeCriptaV2.test_fr319_b_la_cripta_se_carga_y_valida_por_el_servicio_sin_red` |
| FR-320 | H5-3 | `test_api_falsa_v2`: `CasosApendiceB.test_fr320_c_h5_3_tiene_exactamente_los_23_codigos_sin_repetidos`, `CasosApendiceB.test_fr320_c_cada_descripcion_es_la_de_la_tabla_del_contrato`, `CasosApendiceB.test_fr320_c_cada_constructor_da_una_cripta_jugable_sin_red_y_un_guion_con_pasos_conocidos`, `CasosApendiceB.test_fr320_c_llaves_coherentes_con_el_contenido_y_el_catalogo`, `CasosApendiceB.test_fr320_c_b_l6_la_partida_de_la_parte_i_se_rechaza_por_su_version` |
| FR-321 | H5-4 | `test_api_falsa_v2`: `FallosRepetibles.test_fr321_d_h5_4_sin_respuesta_falla_igual_dos_veces`, `FallosRepetibles.test_fr321_d_h5_4_invalida_falla_igual_dos_veces` |
| FR-322, FR-323 | H6-1 | Medición: `--bench llaves`, sección A (`bench/llaves.py`: `_seccion_a`, con `ServicioPrecargaPorCosto` como regla descartada); resultados en [mediciones.md](mediciones.md) |
| FR-324 | H6-2 | [mediciones.md](mediciones.md), «Recomendación sobre la precarga» (mantener por saltos); `precargar_vecinas` y `salas_vecinas` no se modificaron |
| FR-325 | H2-4, H2-5, H2-6 | `test_llaves_partida_cargada`: `CargarNoPide.test_fr325_a_cargar_no_hace_solicitudes_y_deja_llaves_y_aviso_en_none`, `LlavesGuardadas.test_fr325_b_h2_4_con_llaves_guardadas_de_la_misma_version_cero_solicitudes`, `SinLlavesGuardadas.test_fr325_c_h2_5_sin_llaves_guardadas_la_primera_pide_una_vez_y_la_segunda_ninguna`, `SinLlavesYSinPoderPedirlas.test_fr313_fr325_d_h2_6_…` (2 pruebas), `OtraCripta.test_fr325_e_restaurar_otra_cripta_no_arrastra_las_llaves_anteriores`, `LogicaNueva.test_fr325_f_logica_recien_creada_sin_llaves_ni_aviso` |

### Criterios de éxito

| Criterio | Prueba o medición |
|---|---|
| SC-001 | `test_llaves_presupuesto`: `PrimeraPartida.test_fr301_fr304_a_h1_1_…`; `test_llaves_version`: `MismaVersion.test_fr306_a_h2_1_…`; medición `--bench llaves`, sección D (1 / 0 / 0) |
| SC-002 | `test_llaves_fallos`: `ModoSinRed.test_fr312_fr313_c_h3_3_…`, `ModoSinRed.test_fr312_d_h3_4_…`; `test_llaves_clientes`: `MismaListaPorLosTresClientes.test_fr303_e_h5_5_…` (el offline queda en 0); medición `--bench llaves`, sección D |
| SC-003 | `test_fuente_solo_local`: todas las pruebas (comprobación final: espía sin llamadas y bytes iguales), en especial `FichasEnUso.test_sc003_t053_e_fijar_fichas_en_uso_no_escribe_ni_pide` y `SinPrecarga.test_fr316_e_…` |
| SC-004 | `test_llaves_fallos`: `SinRespuesta.test_fr309_fr310_a_h3_1_…`, `RespuestaInvalida.test_fr310_fr311_b_h3_2_…`, `ModoSinRed.test_fr312_fr313_c_h3_3_…`; `test_llaves_presupuesto`: `PresupuestoAgotado.test_fr309_c_sc005_…`, `LimiteDeReintentos.test_sc005_e_…`; `test_fuente_solo_local`: `DatoFaltante.test_fr315_a_h4_1_…`, `VersionDistinta.test_fr317_c_h4_3_…` (los mensajes nombran la cripta y el problema) |
| SC-005 | `test_llaves_presupuesto`: `PresupuestoAgotado.test_fr309_c_sc005_sin_presupuesto_ni_llaves_guardadas_no_consulta_y_avisa_con_la_cripta`, `LimiteDeReintentos.test_sc005_e_con_1_restante_un_429_no_se_reintenta_y_avisa_con_la_cripta`, `LimiteDeReintentos.test_sc005_f_con_3_restantes_429_429_200_hace_3_llamadas_y_devuelve_las_llaves`, `LimiteDeReintentos.test_sc005_g_sin_limite_las_demas_consultas_conservan_max_reintentos_429`; `test_llaves_partida_cargada`: `SinLlavesYSinPoderPedirlas.test_fr313_fr325_d_h2_6_sin_presupuesto_no_pide_y_avisa` |
| SC-006 | `python -m tests_labs.sin_red` (T051: las 9 pruebas, 88 casos, con `requests.get` bloqueado; dos ejecuciones idénticas); `test_sin_red`: `BloqueoDeRed.test_sc006_dentro_de_la_ayuda_requests_get_lanza_intento_de_red`, `BloqueoDeRed.test_sc006_restaura_requests_get_aunque_falle_lo_de_adentro`, `BloqueoDeRed.test_sc006_mock_patch_dentro_de_la_ayuda_sigue_funcionando` |
| SC-007 | Medición `--bench llaves`, sección A (lados 10, 20 y 40); [mediciones.md](mediciones.md) |

### Escenarios

| Escenario | Prueba o medición |
|---|---|
| H1-1 | `PrimeraPartida.test_fr301_fr304_a_h1_1_…` (`test_llaves_presupuesto`) |
| H1-2 | `UbicacionLlavesDelServicio.test_fr302_b_h1_2_…` (`test_llaves_clientes`) |
| H1-3 | `UbicacionLlavesDelServicio.test_fr302_c_h1_3_…` (`test_llaves_clientes`) |
| H1-4 | `UnaVezPorSesion.test_fr301_b_h1_4_…` (`test_llaves_presupuesto`) |
| H1-5 | `UbicacionLlavesDelServicio.test_fr302_d_h1_5_…` (`test_llaves_clientes`); `CasosDeValidacion.test_fr302_fila5_…` (`test_llaves_validacion`) |
| H2-1 | `MismaVersion.test_fr306_a_h2_1_…` (`test_llaves_version`) |
| H2-2 | `OtraVersion.test_fr307_b_h2_2_…` (`test_llaves_version`) |
| H2-3 | `ArchivoDeLaParteI.test_fr308_c_h2_3_…` (`test_llaves_version`) |
| H2-4 | `LlavesGuardadas.test_fr325_b_h2_4_…` (`test_llaves_partida_cargada`) |
| H2-5 | `SinLlavesGuardadas.test_fr325_c_h2_5_…` (`test_llaves_partida_cargada`) |
| H2-6 | `SinLlavesYSinPoderPedirlas.test_fr313_fr325_d_h2_6_…`, 2 pruebas (`test_llaves_partida_cargada`) |
| H3-1 | `SinRespuesta.test_fr309_fr310_a_h3_1_…` (`test_llaves_fallos`) |
| H3-2 | `RespuestaInvalida.test_fr310_fr311_b_h3_2_…` (`test_llaves_fallos`) |
| H3-3 | `ModoSinRed.test_fr312_fr313_c_h3_3_…` (`test_llaves_fallos`) |
| H3-4 | `ModoSinRed.test_fr312_d_h3_4_…` (`test_llaves_fallos`) |
| H4-1 | `DatoFaltante.test_fr315_a_h4_1_…` (`test_fuente_solo_local`) |
| H4-2 | `IgualQueLaViaNormal.test_fr314_fr316_b_h4_2_…` (`test_fuente_solo_local`) |
| H4-3 | `VersionDistinta.test_fr317_c_h4_3_…` (`test_fuente_solo_local`) |
| H5-1 | `Determinismo.test_fr318_a_h5_1_…` (`test_api_falsa_v2`) |
| H5-2 | `ContenidoDeCriptaV2.test_fr319_b_h5_2_…`, 4 pruebas (`test_api_falsa_v2`) |
| H5-3 | `CasosApendiceB.test_fr320_c_h5_3_…` (`test_api_falsa_v2`) |
| H5-4 | `FallosRepetibles.test_fr321_d_h5_4_…`, 2 pruebas (`test_api_falsa_v2`) |
| H5-5 | `MismaListaPorLosTresClientes.test_fr303_e_h5_5_…` (`test_llaves_clientes`) |
| H6-1 | Medición `--bench llaves`, sección A |
| H6-2 | [mediciones.md](mediciones.md), «Recomendación sobre la precarga» |
