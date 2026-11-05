# Mediciones empíricas de laboratorio: Bloque `replay`

**Fecha**: 2026-11-04  
**Comando ejecutado**: `python main.py --bench replay --bench-csv bench_replay_resultados.csv`  
**Entorno de ejecución**: Python 3.12.10, Windows AMD64, Semilla 2026

---

## 1. Sección A: Proporcionalidad temporal (Opción b)

Evaluación en tres escalas de complejidad temporal: 250, 1 000 y 4 000 acciones.  
Para cada escala se compara la ejecución total frente al corte acotado a la mitad del tiempo virtual ($t = T/2$).

| Carga | Acciones | T_total | Eventos Tot. | Eventos T/2 | Razón Eventos | Tiempo Tot (ms) | Tiempo T/2 (ms) | Razón Tiempo |
|---|---|---|---|---|---|---|---|---|
| **250 acciones** | 250 | 25000 | 750 | 375 | **0.500** | 52.0 | 40.3 | 0.776 |
| **1 000 acciones** | 1000 | 100000 | 3000 | 1500 | **0.500** | 122.3 | 74.0 | 0.605 |
| **4 000 acciones** | 4000 | 400000 | 12000 | 6000 | **0.500** | 415.2 | 207.9 | 0.501 |

- **Criterio duro SC-003**: $\text{Razón de Eventos} \le 0.55$ en todas las escalas.
  - 250 acciones: $0.500 \le 0.55$ (**CUMPLE**)
  - 1 000 acciones: $0.500 \le 0.55$ (**CUMPLE**)
  - 4 000 acciones: $0.500 \le 0.55$ (**CUMPLE**)
- **Veredicto de la Sección A**: **CUMPLE**. El costo computacional medido en conteo de eventos procesados es estrictamente proporcional al tiempo virtual $t$ reproducido y no depende del tamaño total del log de partida.

---

## 2. Sección B: Comparación con alternativas descartadas (1 000 acciones, t = 50 001)

El instante de corte (T/2 + 1) cae dentro de una acción del jugador, no sobre uno de sus turnos. Así se mide si cada estrategia ejecuta eventos posteriores a $t$: con $t = T/2$ exacto, la opción a coincidiría con un turno y no se vería la diferencia.

| Estrategia | Eventos procesados | Instante final del reloj | Fidelidad temporal (FR-402 / FR-403) | Proporcionalidad (FR-412) |
|---|---|---|---|---|
| **Opción b (Elegida: tope en ciclo)** | 1500 | 50 000 ($\le t$) | **Cumple** | **Cumple** (proporcional a $t$) |
| **Opción a (Descartada: corte por acción)** | 1503 | 50 100 ($> t$) | **Falla**: avanza hasta el turno siguiente y ejecuta 3 eventos posteriores a $t$ | **Cumple** (corta la lectura del log) |
| **Opción c (Descartada: recorte tras simulación total)** | 3000 | 100 000 | **Cumple** (el estado se reconstruye) | **Falla** (100 % de eventos procesados) |

- **Conclusión técnica**: La **Opción b** es la única que satisface a la vez la fidelidad temporal del enunciado §3.6 (FR-402, FR-403) y el corte proporcional de FR-412. La alternativa a se descarta por la medición: el reloj termina en 50 100, más allá de $t$, y procesa 3 eventos de más.
- Los tiempos de reloj varían entre ejecuciones; el veredicto se toma por conteo de eventos y por el instante final del reloj.

---

## 3. Exportación CSV

Los resultados fueron exportados y verificados en `bench_replay_resultados.csv`:

```csv
seccion,medicion,resultado,unidad
Replay,250 acciones t=T/2,Eventos procesados,375
Replay,1000 acciones t=T/2,Eventos procesados,1500
Replay,4000 acciones t=T/2,Eventos procesados,6000
Replay,1000 acciones t=50001 Opcion B,Eventos procesados,1500
Replay,1000 acciones t=50001 Opcion B,Instante alcanzado,50000
Replay,1000 acciones t=50001 Opcion A,Eventos procesados,1503
Replay,1000 acciones t=50001 Opcion A,Instante alcanzado,50100
Replay,1000 acciones t=50001 Opcion C,Eventos procesados,3000
Replay,1000 acciones t=50001 Opcion C,Instante alcanzado,100000
```
