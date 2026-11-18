# Contrato de Benchmarks: Bloque `replay`

Define la especificación del bloque de evaluación de rendimiento `replay` integrado a la suite `--bench` del sistema (FR-412, FR-413, Principio VII).

---

## 1. Invocación

```bash
python main.py --bench replay
python main.py --bench replay --bench-csv resultados.csv
```

---

## 2. Configuración de cargas de prueba

El benchmark utiliza partidas sintéticas deterministas generadas mediante generadores deterministas por semilla (`semilla=2026`) sobre una cripta sintética fija de referencia.

### Escalas evaluadas

| Escala | Acciones de jugador en el log | Propósito |
|---|---|---|
| **Corta** | 250 acciones | Verificación rápida de sobrecarga fija y consistencia en logs breves. |
| **Media** | 1 000 acciones | Carga estándar para validar proporcionalidad con $t = T/2$ (SC-003). |
| **Larga** | 4 000 acciones | Carga de estrés para demostrar que el costo no depende del tamaño total del log. |

---

## 3. Esquema de reporte en consola

### Sección A: Proporcionalidad del corte temporal (Opción b)

Mide la ejecución de la partida completa frente a la reproducción acotada a la mitad del tiempo virtual ($t = T / 2$):

```text
--- Bloque Replay: Proporcionalidad temporal (Opción b) ---
Carga           Acciones   T_total   Eventos Tot.   Eventos T/2   Razón Ev.   Tiempo Tot (ms)   Tiempo T/2 (ms)   Razón Tiempo
250 acciones         250      2500            820           408       0.498             12.4               6.1          0.492
1000 acciones       1000     10000           3290          1630       0.495             48.2              23.9          0.496
4000 acciones       4000     40000          13150          6540       0.497            192.0              95.4          0.497
```

- **Criterio duro de aprobación**: $\text{Razón de Eventos} \le 0.55$ en todas las escalas (conteo determinista de eventos procesados).
- **Métrica informativa**: $\text{Razón de Tiempo} = \text{Tiempo T/2} / \text{Tiempo Tot}$ (informativa, sensible al ruido del sistema).

---

### Sección B: Comparación con alternativas descartadas

Evalúa en la escala de 1 000 acciones el comportamiento de la opción elegida frente a las alternativas descartadas para $t = T / 2$:

```text
--- Bloque Replay: Comparación con alternativas descartadas (1000 acciones, t = T/2) ---
Estrategia                     Eventos Proc.   Tiempo (ms)   Fidelidad temporal (FR-402/FR-403)   Proporcionalidad (FR-412)
Opción b (Elegida: tope ciclo)          1630          23.9   Cumple (detención exacta en t)       Cumple (proporcional a t)
Opción a (Descartada: corte acc)        1785          26.1   Falla (ejecuta eventos > t)          Cumple (corta lectura log)
Opción c (Descartada: recorte)          3290          48.3   Cumple (estado reconstruido)         Falla (100% de eventos proc)
```

---

## 4. Esquema para `--bench-csv`

Cuando se especifica `--bench-csv <ARCHIVO.csv>`, las filas añadidas siguen la convención estándar del repositorio:

```csv
Subsistema,Escenario,Metrica,Valor
Replay,250 acciones t=T/2,Eventos procesados,408
Replay,250 acciones t=T/2,Tiempo ms,6.1
Replay,1000 acciones t=T/2,Eventos procesados,1630
Replay,1000 acciones t=T/2,Tiempo ms,23.9
Replay,4000 acciones t=T/2,Eventos procesados,6540
Replay,4000 acciones t=T/2,Tiempo ms,95.4
Replay,1000 acciones Opcion A,Eventos procesados,1785
Replay,1000 acciones Opcion C,Eventos procesados,3290
```
