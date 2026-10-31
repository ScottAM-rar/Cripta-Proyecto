# Contrato: qué muestra la consola y de dónde sale

**Requisitos**: FR-216 a FR-219, FR-209. La capa `Vista` solo presenta; la lógica del juego no depende de ella.

## 1. Regla de origen

La vista recibe **únicamente** `MapaConocidoDTO` (ver [data-model.md](../data-model.md)). No recibe `MapaCripta`, ni la lista de salas del modelo, ni el estado real de las puertas. Lo que no está en el DTO no se puede mostrar.

El servicio entrega dos instantáneas:

| Método del servicio | Contenido | Se usa para |
|---|---|---|
| `mapaConocido()` | Todas las salas exploradas, ascendentes por id, con sus salidas, más la sala actual | El comando `mapa` |
| `vistaSalaActual()` | La sala actual con sus salidas, en el mismo formato | La sección «SALIDAS» de cada pantalla |

Ambas se arman al pedirlas; no son una copia viva.

## 2. Sección «SALIDAS» de la sala actual

Cambia respecto de la 001: el destino ya no se muestra como `Sala {id}`.

```text
--- SALIDAS ---
  > Norte -> Pasillo de las urnas [Abierta] costo 100
  > Este  -> sala sin explorar [CERRADA] costo 250
  > Sur   -> Cripta Mayor [Sin observar] costo 100
```

- El destino aparece **con nombre** si está explorado (y puede llevar su id), y como **«sala sin explorar»** si está avistado. Nunca aparece el id ni el nombre de una sala avistada o desconocida.
- El estado de la puerta sale de la puerta **recordada**. En la sala actual coincide siempre con la real (FR-207), de modo que la pantalla no cambia para el jugador.
- «Sin observar» solo puede aparecer en salas exploradas con la antorcha (FR-209).
- La llave requerida por una puerta cerrada, el contenido de la sala actual, los enemigos y las trampas **no** forman parte del conocimiento de las salidas: se siguen mostrando como hasta ahora, porque son de la sala actual (la que el jugador ve). El requisito de llave sigue saliendo de la sala actual del modelo, no del DTO.

## 3. Comando `mapa`

Se escribe `mapa` en el bucle principal (junto a `inventario`, `salir`, etc.). **No es una acción del jugador**: el controlador lo resuelve y vuelve a pedir la orden, sin llamar a `accionJugador`, sin tocar el reloj, el historial del pergamino ni el log (FR-218).

Formato:

```text
==================== MAPA CONOCIDO ====================
Salas exploradas: 3   (estás en la sala marcada con *)
 * Vestíbulo (id 1)
     norte -> Pasillo de las urnas (id 2)   costo 100   abierta
     este  -> sala sin explorar              costo 250   cerrada
   Pasillo de las urnas (id 2)
     sur   -> Vestíbulo (id 1)               costo 100   abierta
     oeste -> sala sin explorar              costo 100   sin observar
```

Reglas:

1. Se listan las salas **exploradas**, en orden **ascendente de id** (FR-217), con su nombre y su id.
2. Por cada sala, sus salidas en el orden en que la sala las declara: dirección, destino, costo y puerta recordada (`abierta`, `cerrada` o `sin observar`).
3. Una sala **avistada** aparece solo como destino «sala sin explorar»; **sin id ni nombre**. Dos salidas hacia la misma sala avistada se muestran idénticas (FR-219).
4. Las salas **desconocidas** no aparecen de ninguna forma.
5. La sala actual se marca con `*`.
6. Con 0 exploradas más allá de la inicial (partida nueva) el mapa muestra la sala inicial con sus salidas.

## 4. Cómo se prueba (sin depender del mapa completo)

`test_niebla_vista.py`:

1. **Vista con el grafo completo apagado.** Se arman a mano un `MapaConocidoDTO` y la sala actual y se llaman `mostrar_mapa_conocido` y `mostrar_juego` **sin pasar `MapaCripta` ni salas**, y con objetos que lanzan error si se tocan colocados donde el modelo habría estado. Debe imprimir el texto esperado.
2. **Sin fugas.** Dos partidas idénticas salvo por nombre, salidas y contenido de salas desconocidas o avistadas imprimen **el mismo** mapa (SC-002).
3. **Búsqueda inversa en el texto.** El texto impreso no contiene el id ni el nombre de ninguna sala avistada o desconocida.
4. **No es una acción.** Tras `mapa`, el reloj, el contador de acciones, el historial del pergamino y el log son idénticos a los de antes.
5. **Salidas de la sala actual.** Una salida hacia una sala avistada no muestra su id.

## 5. Límites

- La presentación textual exacta (columnas, mayúsculas) puede ajustarse; las **reglas 1 a 6 y la regla de origen** no.
- No se muestran costos de rutas ni distancias, solo el costo de cada salida (el viaje es de la 006).
