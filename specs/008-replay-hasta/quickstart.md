# Guía de Validación Rápida (quickstart): Replay Hasta un Instante

Guía práctica de verificación y pruebas automatizadas para la capacidad de reproducción acotada hasta un instante dado.

---

## 1. Pruebas automatizadas

Para ejecutar las pruebas unitarias y de integración de esta capacidad:

```bash
# Ejecutar las pruebas específicas de replay acotado
.venv/Scripts/python.exe -m unittest test_replay_hasta test_determinismo_replay

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
| **FR-401** | Historia 1 (Escenario 1), Historia 2 (Escenario 2) | `test_replay_hasta.py`: `TestArgumentosCLI.test_fr401_hasta_con_replay_valido` |
| **FR-402** | Historia 1 (Escenarios 1, 3) | `test_replay_hasta.py`: `TestTruncamientoTemporal.test_fr402_eventos_mayores_que_t_no_se_ejecutan` |
| **FR-403** | Historia 1 (Escenarios 3, 6) | `test_replay_hasta.py`: `TestTruncamientoTemporal.test_fr403_eventos_de_otros_actores_en_t_se_ejecutan`, `test_fr403_decision_del_jugador_en_t_no_se_ejecuta`, `test_fr403_accion_anterior_a_t_se_ejecuta_completa` |
| **FR-404** | Historia 1 (Escenarios 1 a 6) | `test_replay_hasta.py`: `TestEstadoReportado.test_fr404_contenido_exhaustivo_dto` (incluye estadísticas y efectos activos) |
| **FR-405** | Historia 1 (Escenarios 4, 5, 6) | `test_replay_hasta.py`: `TestCasosLimite.test_fr405_t_mayor_que_final_avisa_log_agotado`, `test_fr405_muerte_antes_de_t`, `test_fr405_partida_termina_exactamente_en_t_sin_aviso` |
| **FR-406** | Historia 1 (Escenario 2) | `test_replay_hasta.py`: `TestCasosLimite.test_fr406_t_igual_cero_sin_acciones` (consecuencia de FR-403, sin regla especial) |
| **FR-407** | Historia 2 (Escenario 1) | `test_replay_hasta.py`: `TestArgumentosCLI.test_fr407_t_negativo_o_no_entero_rechazado` |
| **FR-408** | Historia 2 (Escenario 2) | `test_replay_hasta.py`: `TestArgumentosCLI.test_fr408_hasta_sin_replay_rechazado` |
| **FR-409** | Historia 2 (Escenario 3) | `test_replay_hasta.py`: `TestCompatibilidadReplay.test_fr409_replay_sin_hasta_identico` |
| **FR-410** | Historia 2 (Escenario 4) | `test_replay_hasta.py`: `TestAislamientoReplay.test_fr410_sin_vista_sin_log_sin_puntajes` |
| **FR-411** | Historia 3 (Escenarios 1, 2) | `test_determinismo_replay.py`: `TestDeterminismoReplay.test_fr411_dos_ejecuciones_identicas`, `test_fr411_propiedad_prefijo_equivalente` (el estado en $t$ coincide con el de la reproducción completa en ese instante) |
| **FR-412** | Historia 3 (Escenario 3) | `test_replay_hasta.py`: `TestRendimientoReplay.test_fr412_costo_proporcional_conteo_eventos` |
| **FR-413** | Historia 3 (Escenario 3) | `bench/test_bench_replay.py`: `TestBenchReplay.test_fr413_ejecucion_bloque_bench` |
| **Principio I** | Constitución (Estructuras propias) | Inspección de importaciones y tipos en `DTO/ResultadoReplayHastaDTO.py` y `Logica/EstadoJuegoLogica.py` |
| **Principio IV** | Constitución (Separación MVC) | `test_replay_hasta.py`: verificación de que la lógica devuelve un DTO puro y no escribe en `stdout` |
