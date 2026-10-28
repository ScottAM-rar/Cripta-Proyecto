# Guía de validación (quickstart): Terreno y cazador

Prerrequisitos: Python 3.11+ y `pip install requests`. Todo corre sin red: las pruebas usan la API falsa de `tests_labs/api_falsa.py` y el bench usa criptas sintéticas.

## 1. Pruebas automatizadas

```bash
python -m unittest discover -p "test_*.py"
```

Resultado esperado: todas pasan (120 pruebas al cerrar esta capacidad, de ellas 65 nuevas de esta capacidad en `test_terreno_costos`, `test_cazador`, `test_monticulo_minimo`, `test_equivalencia_cazador`, `test_puertas_punto_unico` y `test_determinismo_cazador`).

## 2. Mediciones

```bash
python main.py --bench terreno
python main.py --bench ciclo,guardado,retroceso
```

Resultado esperado: ciclo < 20 ms con decenas de cazadores; el tiempo del cazador de rango pequeño no crece con N; las alternativas descartadas aparecen medidas; 0 diferencias en la equivalencia. Código de salida distinto de 0 si algún ciclo supera 20 ms. Resultados guardados en [`mediciones.md`](mediciones.md).

## 3. Logs de reproducción

Los `partida.log` de [`replays/`](replays/) citan en su nombre el requisito que demuestran (`FR112_…`, `FR113_…`, `FR114_…`). Se generan con `python -m tests_labs.escenarios_terreno` y los reproduce `test_determinismo_cazador.py` sin vista, con el mismo motor que `--replay`.

Limitación: están grabados sobre la **cripta sintética** de las pruebas, no sobre la del servicio. Para reproducirlos desde `main.py --replay` habría que servir esa misma cripta; la prueba automatizada es la forma soportada.

## 4. Matriz de trazabilidad (requisito → prueba o log)

Comprobada con un recorrido automático de las pruebas, los logs y el bench: ningún FR-101 a FR-131 queda sin cubrir.

| Requisito | Escenarios (spec.md) | Prueba / log |
|---|---|---|
| FR-101, FR-102, FR-124 | Historia 1 (1, 6 a 9); Historia 2 (10) | `test_terreno_costos` (clase `TestCostoDeLasSalidas`), `test_cazador` |
| FR-103, FR-104, FR-105 | Historia 1 (2 a 4) | `test_terreno_costos` (clase `TestMovimientoConCosto`) |
| FR-106, FR-107 | Historia 1 (5, 10) | `test_terreno_costos` |
| FR-108 | Historia 2 (9); casos límite | `test_cazador`, `test_terreno_costos` (persistencia del rango) |
| FR-109 | Historia 2 (8) | `test_cazador` (`TestCazadorEnPartida`) |
| FR-110 a FR-115 | Historia 2 (1 a 7) | `test_cazador`; logs `FR112_…`, `FR113_…`, `FR114_…` |
| FR-116 | Historia 3 (1 a 3) | `test_equivalencia_cazador`, `test_puertas_punto_unico` |
| FR-117 | Historia 3 (4) | `test_cazador`, `test_determinismo_cazador` |
| FR-118, FR-119 | Historia 1 (9, 11, 12) | `test_terreno_costos` (`TestPersistencia`, `TestVista`) |
| FR-120 | Historia 4 (1) | `test_determinismo_cazador` y los tres logs |
| FR-121, FR-122, FR-123 | Historia 4 (2 a 4) | `python main.py --bench terreno` y `--bench ciclo` |
| FR-130, FR-131 | Historia 5 | `test_terreno_costos` (`TestVista`) |
