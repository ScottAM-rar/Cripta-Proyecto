# Guía Rápida de Validación y Trazabilidad: Puntos de Control

**Capacidad**: `007-puntos-de-control` | **Fecha**: 2026-11-07 | **Especificación**: [spec.md](spec.md)

Esta guía detalla los comandos de ejecución y validación de la capacidad, junto con la matriz integral de trazabilidad que vincula cada requisito funcional con sus escenarios de aceptación y pruebas automatizadas.

---

## 1. Escenarios de Ejecución y Validación

### 1.1. Validación temprana en CLI (Rechazo sin iniciar)
Verifica que argumentos inválidos no instancian el servicio ni tocan disco (salida con código 2):

```powershell
# K inválidos: deben fallar con código 2 y mensaje explicativo
.venv\Scripts\python.exe main.py --checkpoint-cada 0
.venv\Scripts\python.exe main.py --checkpoint-cada -5
.venv\Scripts\python.exe main.py --checkpoint-cada 2.5
.venv\Scripts\python.exe main.py --checkpoint-cada abc

# K válido: inicia el juego e informa K antes de la primera decisión
.venv\Scripts\python.exe main.py --checkpoint-cada 10
```

### 1.2. Ejecución de la Suite de Pruebas Automatizadas
Todas las pruebas unitarias y de integración de la capacidad se ejecutan mediante `unittest`:

```powershell
# Pruebas de validación de CLI y configuración de K
.venv\Scripts\python.exe -m unittest test_cli_checkpoint

# Pruebas de captura de puntos, contador temporal y poda por pergamino
.venv\Scripts\python.exe -m unittest test_puntos_control

# Pruebas de determinismo e invariancia de la partida con distintos valores de K
.venv\Scripts\python.exe -m unittest test_determinismo_puntos_control

# Pruebas de persistencia binaria v7 y rechazo explícito de versiones anteriores
.venv\Scripts\python.exe -m unittest test_persistencia_v7

# Ejecutar todas las pruebas de la capacidad juntas
.venv\Scripts\python.exe -m unittest discover -p "test_*puntos_control*.py"
```

### 1.3. Medición de Rendimiento con `--bench`
Ejecución del bloque de benchmark en criptas sintéticas deterministas por semilla:

```powershell
# Ejecución exclusiva del bloque puntos_control
.venv\Scripts\python.exe main.py --bench puntos_control

# Ejecución con reporte CSV (no versionado)
.venv\Scripts\python.exe main.py --bench puntos_control --bench-csv bench_checkpoints.csv
```

---

## 2. Matriz de Trazabilidad: Requisitos → Escenarios → Pruebas

| Requisito | Descripción sucinta | Escenario de Aceptación (`spec.md`) | Prueba / Verificación |
|---|---|---|---|
| **FR-414** | Bandera `--checkpoint-cada K` con entero $\ge 1$ | Historia 1, Escenario 1 y 2 | `test_cli_checkpoint.py:test_k_valido_inicia` |
| **FR-415** | Valor mínimo permitido $K = 1$ | Historia 1, Escenario 2 | `test_cli_checkpoint.py:test_k_minimo_uno` |
| **FR-416** | Valor por defecto de $K$ e informe inicial | Historia 1, Escenario 3 | `test_cli_checkpoint.py:test_k_defecto_reportado` |
| **FR-417** | Rechazo de 0, negativos, decimales y texto | Historia 1, Escenarios 4, 5, 6, 7 | `test_cli_checkpoint.py:test_k_invalido_rechazado` |
| **FR-418** | Punto 0 inicial, punto periódico cada $n \times K$, conteo de acciones y descarte por pergamino | Historia 2, Escenarios 1, 2; Casos límite | `test_puntos_control.py:test_captura_inicial_y_periodica`, `test_poda_pergamino` |
| **FR-419** | No más de un punto de control cada $K$ acciones | Historia 2, Escenario 2 | `test_puntos_control.py:test_distribucion_estricta_k` |
| **FR-420** | Transparencia: sin mensajes ni pausas visibles | Historia 2, Escenario 3 | `test_puntos_control.py:test_silencio_interfaz` |
| **FR-421** | Copia completa del estado (reloj, jugador, azar, etc.) | Historia 2, Escenario 4 | `test_puntos_control.py:test_integridad_estado_guardado` |
| **FR-422** | Reanudar desde punto de control es 100% reproducible | Historia 3, Escenario 1 | `test_determinismo_puntos_control.py:test_reanudacion_identica` |
| **FR-423** | Elección de $K$ no cambia el resultado final de la partida | Historia 3, Escenarios 2, 3 | `test_determinismo_puntos_control.py:test_invarianza_desenlace_k` |
| **FR-424** | Guardar y cargar conserva puntos de control y K | Historia 4, Escenario 1 | `test_persistencia_v7.py:test_guardar_cargar_conserva_puntos` |
| **FR-425** | Rechazo explícito de versiones anteriores (v6 o Parte I) | Historia 4, Escenario 2 | `test_persistencia_v7.py:test_rechazo_v6_y_anteriores` |
| **FR-426** | Ciclo de eventos $\le 20$ ms con $K=1$ en `--bench` | Historia 5, Escenarios 1, 2 | `bench/puntos_control.py`, `test_bench_puntos_control.py` |
