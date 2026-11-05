# Guía de Validación Rápida (quickstart): Replay Hasta un Instante

Guía práctica de verificación y pruebas automatizadas para la capacidad de reproducción acotada hasta un instante dado.

---

## 1. Pruebas automatizadas

Para ejecutar las pruebas unitarias y de integración de esta capacidad:

```bash
# Ejecutar las pruebas específicas de replay acotado
.venv/Scripts/python.exe -m unittest test_replay_hasta test_determinismo_replay test_rendimiento_replay bench.test_bench_replay

# Verificar que la suite completa de pruebas del repositorio sigue pasando sin regresiones
.venv/Scripts/python.exe -m unittest discover -p "test_*.py"
```

---

## 2. Medición de rendimiento

Para ejecutar el bloque de benchmark de reproducción:

```bash
# Ejecutar únicamente el bloque de replay
.venv/Scripts/python.exe main.py --bench replay

# Ejecutar y exportar resultados a CSV
.venv/Scripts/python.exe main.py --bench replay --bench-csv resultados_replay.csv
```

**Resultado esperado**:
- La Sección A debe reportar una razón de eventos procesados $\le 0.55$ en $t = T/2$ para las cargas de 250, 1 000 y 4 000 acciones.
- La Sección B debe evidenciar que la Opción b cumple tanto con la fidelidad temporal (FR-402, FR-403) como con el corte efectivo de eventos frente a las alternativas a y c.

---

## 3. Verificación manual por consola

```bash
# 1. Validación de rechazo: --hasta sin --replay
.venv/Scripts/python.exe main.py --hasta 100
# Esperado: Mensaje de error indicando que --hasta requiere --replay y código de salida 2.

# 2. Validación de rechazo: t negativo o no entero
.venv/Scripts/python.exe main.py --replay partida.log --hasta -5
.venv/Scripts/python.exe main.py --replay partida.log --hasta texto
# Esperado: Error de validación de argumento de argparse y código de salida 2.

# 3. Reproducción acotada a instante 0
.venv/Scripts/python.exe main.py --replay partida.log --hasta 0
# Esperado: 0 acciones reproducidas, instante alcanzado 0 y el estado inicial real en pantalla (la primera decisión del jugador es en el instante 0 y no se ejecuta).

# 4. Reproducción acotada a instante intermedio
.venv/Scripts/python.exe main.py --replay partida.log --hasta 500
# Esperado: Se detiene en o antes de t=500 y reporta el estado exhaustivo del jugador y sala.

# 5. Reproducción estándar sin --hasta (regresión)
.venv/Scripts/python.exe main.py --replay partida.log
# Esperado: Muestra exactamente el formato clásico sin alterar la salida existente.
```

---

## 4. Matriz de trazabilidad (Requisito → Escenario → Prueba)

Cada requisito funcional de `spec.md` cuenta con una o más pruebas automatizadas que citan explícitamente su identificador `FR-4xx`:

| Requisito | Escenario en `spec.md` | Prueba automatizada |
|---|---|---|
| **FR-401** | Historia 1 (Escenario 1), Historia 2 (Escenario 2) | `test_replay_hasta.py`: `TestEstadoReportado.test_FR401_FR404_campos_exhaustivos` |
| **FR-402** | Historia 1 (Escenario 1, 3) | `test_replay_hasta.py`: `TestTruncamientoTemporal.test_FR402_no_desapila_eventos_posteriores_al_tope`, `test_FR402_turno_jugador_posterior_permanece_en_reloj`; `bench/test_bench_replay.py`: `TestBenchReplay.test_alternativa_a_ejecuta_eventos_posteriores_a_t` |
| **FR-403** | Historia 1 (Escenarios 3, 6) | `test_replay_hasta.py`: `TestTruncamientoTemporal.test_FR403_completar_instante_ejecuta_eventos_de_otros_actores_en_tope`, `test_FR403_decision_jugador_en_tope_no_se_ejecuta`, `test_FR402_FR403_accion_jugador_anterior_a_tope_se_ejecuta_completa` |
| **FR-404** | Historia 1 (Escenarios 1 a 6) | `test_replay_hasta.py`: `TestEstadoReportado.test_FR401_FR404_campos_exhaustivos` (incluye estadísticas y efectos activos), `TestCasosLimite.test_FR404_FR405_muerte_antes_de_alcanzar_t_congela_reloj` |
| **FR-405** | Historia 1 (Escenarios 4, 5, 6) | `test_replay_hasta.py`: `TestCasosLimite.test_FR405_log_agotado_antes_de_alcanzar_t`, `test_FR404_FR405_muerte_antes_de_alcanzar_t_congela_reloj`, `test_terminacion_exactamente_en_t` |
| **FR-406** | Historia 1 (Escenario 2) | `test_replay_hasta.py`: `TestCasosLimite.test_FR406_hasta_cero_no_ejecuta_ninguna_accion` (consecuencia de FR-403, sin regla especial) |
| **FR-407** | Historia 2 (Escenario 1) | `test_replay_hasta.py`: `TestArgumentosCLI.test_FR407_rechaza_valor_negativo`, `test_FR407_rechaza_valor_no_entero`, `test_SC004_latencia_rechazo_menor_a_100ms` |
| **FR-408** | Historia 2 (Escenario 2) | `test_replay_hasta.py`: `TestArgumentosCLI.test_FR408_rechaza_hasta_sin_replay`, `test_SC004_latencia_rechazo_menor_a_100ms` |
| **FR-409** | Historia 2 (Escenario 3) | `test_replay_hasta.py`: `TestCompatibilidadReplay.test_FR409_replay_sin_hasta_retorna_lista_eventos` |
| **FR-410** | Historia 2 (Escenario 4) | `test_replay_hasta.py`: `TestAislamientoReplay.test_FR410_no_crea_nuevos_logs_ni_puntajes` |
| **FR-411** | Historia 3 (Escenarios 1, 2) | `test_determinismo_replay.py`: `TestDeterminismoReplay.test_FR411_determinismo_estricto_dos_ejecuciones_identicas`, `test_FR411_propiedad_de_prefijo` (el estado en $t$ coincide con el de la reproducción completa en ese instante) |
| **FR-412** | Historia 3 (Escenario 3) | `test_rendimiento_replay.py`: `TestRendimientoReplay.test_FR412_SC003_escala_250_acciones`, `test_FR412_SC003_escala_1000_acciones`, `test_FR412_SC003_escala_4000_acciones` |
| **FR-413** | Historia 3 (Escenario 3) | `bench/test_bench_replay.py`: `TestBenchReplay.test_ejecutar_benchmark_replay` |
| **Principio I** | Constitución (Estructuras propias) | Inspección de importaciones y tipos en `DTO/ResultadoReplayHastaDTO.py` y `Logica/EstadoJuegoLogica.py` |
| **Principio IV** | Constitución (Separación MVC) | `test_replay_hasta.py`: verificación de que la lógica devuelve un DTO puro y no escribe en `stdout` |
