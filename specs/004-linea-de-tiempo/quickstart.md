# Guía de validación rápida y trazabilidad (004-linea-de-tiempo)

**Capacidad**: `004-linea-de-tiempo`  
**Fecha**: 2026-11-08  

Esta guía describe cómo verificar la capacidad de consulta de estados pasados (`historia <t>` e `historia #k`) de forma interactiva, mediante pruebas unitarias automatizadas y con la suite de benchmark.

---

## 1. Pruebas Unitarias Automatizadas

Ejecutar la suite completa de pruebas de la capacidad desde la raíz del repositorio:

```bash
# Probar la firma existente para asegurar retrocompatibilidad
.venv/Scripts/python.exe -m unittest test_historia_firma.py

# Probar la funcionalidad completa de la línea de tiempo (FR-427 a FR-443)
.venv/Scripts/python.exe -m unittest test_historia_tiempo.py

# Probar el aislamiento estricto y la integración con el pergamino y persistencia
.venv/Scripts/python.exe -m unittest test_historia_aislamiento.py
```

---

## 2. Validación Interactiva Manual (Partida de ~30 acciones)

Para verificar visualmente la interfaz y el comportamiento durante el juego:

1. Iniciar una partida interactiva offline:
   ```bash
   .venv/Scripts/python.exe main.py --offline --checkpoint-cada 5
   ```
2. Realizar una secuencia de acciones variadas:
   - Recoger objetos (`recoger antorcha`, etc.).
   - Moverse por varias salas (`norte`, `este`, `sur`).
   - Esperar algunos turnos (`esperar`).
   - Usar un pergamino de retroceso si está disponible.
3. Consultar la historia por tiempo y acción:
   - `historia 0`: Debe mostrar la sala inicial, vida completa, antes de la primera decisión.
   - `historia #1`: Debe ser idéntico a `historia 0`.
   - `historia 150`: Debe mostrar el estado exacto en $t = 150$.
   - `historia #5`: Debe mostrar el estado justo antes de tomar la 5ª acción.
4. Probar casos inválidos:
   - `historia 99999`: Debe responder con aviso de instante futuro sin romper la partida.
   - `historia #0`: Debe indicar que la acción debe ser $\ge 1$.
   - `historia #999`: Debe responder con aviso de acción futura.
   - `historia abc`: Debe indicar formato no reconocido.
5. Continuar jugando tras las consultas:
   - Moverse a otra sala: verificar que el juego responde normalmente, el reloj sigue avanzando desde donde estaba y el historial del pergamino sigue funcionando.
6. Probar en partida terminada:
   - Al morir o ganar la partida, en el prompt final escribir `historia 0` o `historia #3` y comprobar que responde correctamente con el estado histórico.

---

## 3. Ejecución de Benchmarks de Rendimiento

Para medir el rendimiento frente al límite de 50 ms y contrastar con las alternativas descartadas:

```bash
# Ejecutar el bloque específico de historia
.venv/Scripts/python.exe main.py --bench historia

# O ejecutar todos los benchmarks incluyendo puntos de control e historia
.venv/Scripts/python.exe main.py --bench puntos_control,historia
```

### Criterios de aceptación medibles en `--bench`:
- Con 5 000 acciones y $K = 10$, ninguna consulta `historia` supera **50 ms** (FR-442, SC-006).
- El tiempo de búsqueda binaria en lista de checkpoints se contrasta frente al recorrido lineal.
- Se mide la alternativa descartada (reconstrucción desde el inicio, sin puntos de control), comprobando que el enfoque elegido es órdenes de magnitud más rápido.

---

## 4. Matriz de Trazabilidad de Requisitos (FR-427 a FR-443)

| Requisito | Descripción | Componente | Prueba Automatizada | Escenario Apéndice B |
|---|---|---|---|---|
| **FR-427** | Comando `historia <t>` en partida interactiva y concluida | `EstadoJuegoServicio`, `ControladorJuego` | `test_historia_tiempo.py::test_partida_terminada_acepta_consultas`, `test_historia_tiempo.py::test_comandos_historia_en_controlador_no_alteran_partida`, `test_historia_firma.py::test_por_instante_y_por_accion_devuelven_un_resumen` | Caso 3 (múltiples eventos en $t$) |
| **FR-428** | Estado en $t$ justo antes de la decisión del jugador | `EstadoJuegoLogica._reconstruirHastaInstante` | `test_historia_tiempo.py::test_corte_instante_decision_jugador_y_eventos_enemigo` | Caso 3 |
| **FR-429** | Comando `historia #k` en partida viva y concluida | `EstadoJuegoServicio`, `ControladorJuego` | `test_historia_accion.py::test_equivalencia_accion_instante_partida_40_acciones`, `test_historia_accion.py::test_partida_terminada_acepta_consultas_intermedias` | — |
| **FR-430** | `historia #1` y `historia 0` devuelven estado inicial | `EstadoJuegoLogica` | `test_historia_tiempo.py::test_historia_cero_da_estado_inicial`, `test_historia_accion.py::test_historia_1_equivale_a_historia_cero` | — |
| **FR-431** | Contenido mínimo del estado reportado (vida, sala, stats, inv, etc.) | `ResumenEstadoDTO`, `VistaConsola` | `test_historia_tiempo.py::test_FR431_contenido_minimo_del_estado_en_el_dto_y_en_la_vista` | — |
| **FR-432** | Consulta no altera partida viva (reloj, log, pergamino, azar) | `EstadoJuegoLogica.consultarHistoria` | `test_historia_aislamiento.py::test_invariancia_reloj_acciones_y_puntaje`, `test_historia_aislamiento.py::test_invariancia_bitacora_y_log_memoria_y_disco`, `test_historia_aislamiento.py::test_invariancia_generadores_de_azar`, `test_historia_aislamiento.py::test_invariancia_singleton_retroceso_y_puntero_reloj`, `test_historia_aislamiento.py::test_invariancia_exportar_estado_completo` | Caso 4 (consulta no altera partida) |
| **FR-433** | Rechazo de $t > \text{reloj actual}$ con mensaje claro | `EstadoJuegoServicio`, `ControladorJuego` | `test_historia_tiempo.py::test_t_igual_al_reloj_vivo_y_rechazo_de_futuro_y_tipos_invalidos`, `test_historia_pergamino.py::test_instante_revertido_rechazado_como_futuro` | Caso 1 (tiempo futuro) |
| **FR-434** | Coherencia con pergamino: acciones revertidas no existen en la historia | `EstadoJuegoLogica`, `RetrocesoLogica` | `test_historia_pergamino.py::test_revertir_3_de_10_acciones_invisibilidad_revertidas_y_linea_vigente`, `test_historia_accion.py::test_secuencia_A1_A2_A3_P_A3p_A4` | Caso 2 (coherencia con retroceso) |
| **FR-435** | Rechazo de $k \le 0$ | `EstadoJuegoServicio` | `test_historia_accion.py::test_accion_cero_rechazada`, `test_historia_accion.py::test_negativos_rechazados` | — |
| **FR-436** | `k = N+1` da estado actual; `k > N+1` se rechaza | `EstadoJuegoServicio`, `EstadoJuegoLogica` | `test_historia_accion.py::test_historia_N_mas_1_devuelve_estado_vivo`, `test_historia_accion.py::test_historia_mayor_N_mas_1_rechazada` | — |
| **FR-437** | Rechazo de valores no numéricos, decimales o negativos | `EstadoJuegoServicio`, `ControladorJuego` | `test_historia_firma.py::test_rechaza_negativos_y_no_enteros`, `test_historia_accion.py::test_floats_rechazados`, `test_historia_accion.py::test_strings_rechazados`, `test_historia_accion.py::test_bool_rechazado`, `test_historia_tiempo.py::test_t_igual_al_reloj_vivo_y_rechazo_de_futuro_y_tipos_invalidos` | — |
| **FR-438** | Partida sin acciones: `0` y `#1` permitidos, futuros rechazados | `EstadoJuegoLogica` | `test_historia_accion.py::test_partida_sin_acciones_accion_1_es_inicial`, `test_historia_accion.py::test_partida_sin_acciones_accion_2_rechazada` | — |
| **FR-439** | Reconstrucción no requiere más de $K$ acciones | `EstadoJuegoLogica` | `test_historia_tiempo.py::test_FR439_reconstruir_no_aplica_mas_de_k_acciones_desde_el_punto_cercano` | — |
| **FR-440** | Reconstrucción no hace solicitudes de red | `EstadoJuegoServicio` | `test_historia_aislamiento.py::test_auditoria_red_cero_solicitudes_y_sin_llamadas_prohibidas`, `test_historia_movimiento.py::test_cache_muy_pequena_no_provoca_solicitudes` | — |
| **FR-441** | Guardar y cargar (formato vigente, v7 o posterior) conserva la línea de tiempo | `AlmacenPartidaBinario`, `EstadoJuegoServicio` | `test_historia_persistencia.py::test_guardar_y_cargar_con_movimiento_pergamino_y_oraculo`, `test_historia_persistencia.py::test_consulta_no_modifica_ni_crea_archivo_guardado`, `test_historia_persistencia.py::test_cargar_con_otro_k_no_rompe_consultas` | Caso 6 (persistencia v7) |
| **FR-442** | Rendimiento $\le 50$ ms con 5 000 acciones al $K$ por defecto | `bench/historia.py` | `bench/test_bench_historia.py` | — |
| **FR-443** | Interfaz interactiva reconoce `historia <t>` e `historia #k` | `ControladorJuego`, `VistaConsola` | `test_historia_tiempo.py::test_comandos_historia_en_controlador_no_alteran_partida` | — |

---

## 5. Casos de Prueba Críticos de Aislamiento e Integración

1. **Aislamiento de `RetrocesoLogica`**:
   - Realizar 3 acciones con el jugador.
   - Ejecutar `historia <t>`.
   - Usar un pergamino en la partida viva: debe revertir con éxito la 3ª acción, demostrando que el historial del singleton no se corrompió ni se vació.
2. **Determinismo del azar**:
   - Registrar `juego.gestorEventos.azar.getstate()`.
   - Ejecutar 10 consultas `historia`.
   - Comparar el estado del azar: debe ser idéntico al registrado.
3. **Invarianza de red**:
   - `servicio.reporteSolicitudes()` antes y después de `consultarHistoria()` muestra idéntico número de solicitudes.
4. **Consulta en partida cargada de archivo v7**:
   - Jugar 15 acciones con $K = 5$, guardar en archivo binario v7.
   - Cargar en nueva sesión con `cargarPartida()`.
   - Ejecutar `historia #3` y `historia <t>`: los estados devueltos coinciden exactamente con los de la sesión original.
