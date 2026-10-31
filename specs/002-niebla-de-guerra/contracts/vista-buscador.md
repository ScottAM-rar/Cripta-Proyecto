# Contrato: vista del conocimiento para `BuscadorRutas`

**Consume**: la especificación 006 «ir a» (fuera del alcance de esta capacidad). **Produce**: `VistaMapaConocido` en `Logica/MapaConocido.py`. **Requisitos**: FR-216, FR-219 (la vista solo conoce lo que el jugador conoce); sustenta la futura 006.

Aquí **solo se define el contrato y se entrega la vista**. El viaje (elegir un destino, avanzar paso a paso, reaccionar a una puerta que resultó cerrada) no se implementa.

## 1. Interfaz

`BuscadorRutas.distancias_hacia(destino, vista, limite)` exige una vista con:

| Miembro | Tipo | Contrato |
|---|---|---|
| `tamano` | entero | El mismo `tamano` de `MapaCripta` (cota de ids; la posición 0 no se usa) |
| `salidas(sala)` | lista de aristas | Las aristas del esqueleto que salen de `sala` **si `sala` está explorada**; lista vacía si no (de una sala no explorada no se conocen sus salidas) |
| `entrantes(sala)` | lista de aristas | Las aristas del esqueleto que llegan a `sala` **si `sala` está explorada**; vacía si no |
| `transitable(arista)` | booleano | Verdadero solo si: el origen está explorado **y** el destino está explorado **y** la puerta recordada de esa salida es «abierta» |

Cada arista conserva sus campos del esqueleto (`origen`, `direccion`, `destino`, `costo`), de modo que el costo que usa la búsqueda es el que el jugador conoce (FR-206).

Además, para quien guarde un resultado:

| Miembro | Contrato |
|---|---|
| `version_conocimiento` | Entero que sube con **todo** cambio de estado de sala o de puerta recordada, hacia adelante o al deshacer. Si no cambió, lo guardado sigue valiendo |

## 2. Qué garantiza

1. **Solo conocimiento del jugador.** Una ruta calculada con esta vista pasa únicamente por salas exploradas y por salidas recordadas como abiertas. Nunca consulta el estado real de una puerta ni una sala no explorada.
2. **Consulta O(1)** por llamada, sin copiar el esqueleto ni el conocimiento. Las listas devueltas son las internas del esqueleto: **no se deben modificar** (igual que en `MapaCripta`).
3. **Siempre vigente.** Como lee los arreglos del conocimiento, refleja el estado actual sin reconstrucciones.
4. **Determinista.** No depende de qué contenido esté descargado.

## 3. Qué NO garantiza (límites que la 006 debe contemplar)

- Una puerta «abierta» es lo que el jugador **recuerda**: puede estar cerrada en realidad (FR-208). Una ruta válida en la vista puede toparse con una puerta cerrada; qué hacer entonces lo decide la 006.
- El **destino** de un viaje debe estar explorado; una sala solo avistada no tiene salidas conocidas y la búsqueda no entra a ella por las aristas entrantes.
- Una puerta «sin observar» (FR-209) **no** es transitable en esta vista.
- No incluye costos de descubrir salas nuevas ni exploración por antorcha.

## 4. Alternativa descartada

Materializar un `MapaCripta` nuevo con solo las salas exploradas: cuesta reconstruirlo ante cada cambio del conocimiento y duplica memoria. Se mide en `--bench mapa` (sección G) para respaldar la decisión.

## 5. Pruebas que lo cubren

`test_vista_conocimiento_buscador.py`: una `BuscadorRutas` real sobre la vista no atraviesa salas no exploradas ni puertas recordadas cerradas o sin observar; el costo hallado coincide con el de un mapa materializado de referencia; `version_conocimiento` sube al explorar, al observar y al deshacer, y no sube al consultar.
