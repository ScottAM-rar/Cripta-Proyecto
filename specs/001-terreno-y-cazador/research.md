# Investigación (Fase 0): Terreno y cazador

Todas las decisiones de este documento son de **cómo**; las reglas del juego están solo en `spec.md`. No quedan marcadores `NEEDS CLARIFICATION` en el contexto técnico.

## 1. Dónde vive la información del esqueleto

**Hallazgo**: `ServicioCripta` ya descarga el esqueleto completo al iniciar y lo guarda como lista de diccionarios crudos. Las salas del juego (`SalaDTO`) se arman de forma perezosa y `EstadoJuegoLogica.salas` tiene `None` en las no cargadas. El rastreador ya tiene que preguntar `sala is None`.

**Decisión**: construir, una vez al iniciar, un `MapaCripta` a partir del esqueleto ya descargado y entregarlo al modelo por la interfaz de fuente de datos (`FuenteCripta`). Cero solicitudes nuevas.

**Estado de las puertas**: la verdad sigue en los `SalidaDTO` de las salas cargadas. Para una sala no cargada vale el estado inicial del esqueleto. Esto es equivalente a tener todas cargadas, porque una puerta solo puede cambiar en una sala cargada. Así se cumple FR-117 sin duplicar estado.

**Alternativas descartadas**:
- Cargar todas las salas (contenido) para que el cazador mire `salas[i]`. Gasta solicitudes (VI) y haría la decisión dependiente de lo descargado (II, FR-117).
- Copiar el estado de las puertas dentro del mapa. Dos fuentes de verdad que sincronizar; riesgo de decisiones obsoletas (III).

## 2. Forma del mapa y del campo de costos

**Decisión**:
- Aristas salientes por sala en `list` de `list`, indexadas por id de sala (los ids son densos desde 1, ya supuesto en la Parte I; tamaño = mayor id + 1).
- Aristas **entrantes** por sala en otra lista del mismo estilo. Permiten la búsqueda desde el jugador hacia atrás sin suponer que toda salida tiene su inversa.
- Campo de costos: dos `list` de tamaño N (costo y marca de época), asignadas una sola vez.
- Búsqueda de menor costo desde la sala del jugador sobre las aristas entrantes, con un montículo binario propio con clave `(costo, id de sala)`. Se detiene al sacar un costo mayor que la cota.
- Reinicio en O(1) por **marca de época**: en vez de limpiar N posiciones se incrementa un contador; una posición solo vale si su marca es la época actual. Es lo que hace que el costo dependa de la región explorada y no de N (FR-122).

**Cota**: el mayor rango entre los cazadores que consultan. Todo nodo con costo ≤ cota queda con costo exacto; todo nodo no alcanzado tiene costo > cota. Por eso un cazador cuyo rango es ≤ cota decide igual que con una búsqueda sin cota. La cota solo cambia cuánto se explora, nunca la decisión.

**Alternativas descartadas** (todas se miden en `--bench`, VII):
- Búsqueda hacia adelante por cada cazador (de su sala al jugador). Multiplica el trabajo por la cantidad de cazadores y obliga a una segunda pasada para el desempate de vecinos.
- Búsqueda sin cota sobre toda la cripta. Costo proporcional a N (viola FR-122).
- Matriz de costos entre pares de salas. Memoria O(N²) y no sirve con criptas mayores.
- Reutilizar un cálculo anterior sin invalidación. Viola III.

## 3. Montículo: ¿se reutiliza el del reloj?

**Hallazgo**: `RelojVirtual` tiene su propio montículo binario, pero está acoplado a `EventoDTO` (campo `posicion`, comparación por tiempo y secuencia, registro de retroceso).

**Decisión**: escribir `MonticuloMinimo` genérico y pequeño, sin tocar el del reloj. La constitución pide reutilizar estructuras de la Parte I "si son adecuadas"; esta no lo es sin modificar código de la Parte I que ya funciona y está medido. Para la búsqueda se usa entrada duplicada con descarte al sacar (no hace falta disminuir clave).

## 4. Invalidación del campo, razonada por evento (principio III)

El campo guarda: sala del jugador de origen, cota, y un contador de cambios de puertas. Es válido solo si todos coinciden.

| Evento | ¿Puede cambiar una decisión? | Acción |
|---|---|---|
| El jugador cambia de sala (movimiento, retroceso, restauración) | Sí: cambia el origen | Invalidar |
| Se cierra la puerta de la salida x→y | Solo si y está dentro del campo (la arista x→y se usa al procesar y) | Invalidar si y fue alcanzado; si no, no hace falta |
| Se abre la puerta de x→y | Solo si y está dentro del campo (puede acortar el costo de x) | Invalidar si y fue alcanzado; si no, no hace falta |
| Un cazador (u otro actor) se mueve, ataca o muere | No: los actores no bloquean salidas ni cambian costos | Nada |
| Un cazador nuevo se activa con rango mayor que la cota | Sí: la zona explorada es insuficiente | Recalcular con la cota mayor |
| Carga de partida guardada | Sí | Descartar el campo |
| Cambia el costo de una salida | No ocurre en juego: el costo es estático | — |

**Punto único de cambio de puertas**: para que ningún cambio pase sin avisar, toda modificación de `cerrada` pasa por una sola función en `SalasLogica` (abrir, cerrar por evento automático, deshacer por pergamino, restaurar partida). Una prueba recorre el código y falla si aparece otra escritura de `.cerrada`.

**Equivalencia (prueba)**: `test_equivalencia_cazador.py` genera cripta y secuencias de eventos con semilla, y tras cada evento compara la decisión del cazador usando el campo reutilizado con la decisión usando un cálculo hecho desde cero. Cualquier diferencia hace fallar la prueba.

## 5. Costo del movimiento y siguiente evento

**Hallazgo**: `EnemigoLogica.decidirAccion` programa siempre el siguiente evento con costo 100; el controlador arma `MOVER_JUGADOR` con costo 100; `ActorLogica._mover` no informa nada.

**Decisión**:
- `_mover` informa el costo de la salida cruzada.
- El contrato de los comportamientos pasa de devolver un texto a devolver `AccionEnemigoDTO(mensaje, costo)`. Para errante, rastreador y guardián solo cambia el costo del movimiento (FR-106); esperar, atacar y "no se movió" siguen en 100 (FR-107).
- Los comportamientos reciben un parámetro opcional con el campo de costos; solo el cazador lo usa.
- El controlador construye `MOVER_JUGADOR` con el costo de la salida elegida. La fórmula de intervalo no cambia (FR-104). El cambio de velocidad en pleno cruce ya reescala el tiempo restante (FR-105, regla existente).
- La repetición (`--replay`) lee el costo grabado en el log, así que sigue funcionando con logs de la Parte I.

**Alternativa descartada**: deducir el costo comparando la sala anterior y la nueva. Es ambiguo si dos salidas llevan a la misma sala con costos distintos.

## 6. Datos inválidos (clarificaciones 2 y 3)

- Costo inválido (cero, negativo, no entero, booleano): se usa 100 y se registra una advertencia. La validación ocurre al construir el mapa y al armar las salidas, en el adaptador, no en el modelo.
- Rango ausente o inválido: 0 con advertencia; rango 0 declarado es válido.
- Las advertencias se acumulan en el servicio y las muestra la vista al iniciar; el modelo solo las expone como una lista.

## 7. Versiones y persistencia (principio VI, FR-119)

- Caché de esqueleto y catálogo: ya se valida por versión de cripta y de catálogo. Un esqueleto guardado sin `costo` es compatible (ausente = 100). Si el servidor publica costos nuevos, publica nueva versión y el mecanismo existente lo invalida sin borrar archivos.
- Guardado binario: se agregan `costo` por salida y `rango` por enemigo. `VERSION_ESTADO` pasa de 2 a 3 y `VERSION_FORMATO` de 5 a 6. Un archivo de versión anterior se **rechaza** con mensaje explícito (no se migra: no tiene cazadores ni costos, y la partida en curso no se puede continuar con seguridad). Los campos nuevos van al final de sus DTO; el orden de `CLASES_DTO` no cambia.

## 8. Rendimiento y mediciones planificadas (principio VII)

Bloque nuevo `terreno` de `--bench`, con criptas sintéticas deterministas por semilla:

| Sección | Qué compara | Límite / criterio |
|---|---|---|
| Un cazador frente a muchos (1, 10, 50, 200) | Campo compartido vs. búsqueda por cazador (alternativa descartada) | Ciclo < 20 ms con decenas |
| Rango pequeño frente a grande, con N creciente | Búsqueda acotada vs. búsqueda sin cota (alternativa descartada) | Con rango pequeño, tiempo ≈ constante al crecer N |
| Puertas estables frente a cambiantes | Invalidación por evento vs. invalidar con cualquier cambio de puerta (alternativa descartada) | Informar la ganancia |
| Equivalencia | Decisión con campo vs. desde cero tras cada tipo de evento | 100 % idénticas |

Además se repiten con la carga nueva las mediciones de la Parte I que esta capacidad puede afectar: `ciclo` (ahora con cazadores), `guardado` (campos nuevos) y `retroceso` (cambios de puertas por el punto único). Si una decisión deja de servir se cambia y se documenta el antes y el después en `DECISIONES.md`.

## 9. Riesgos y huecos conocidos

- **Costos distintos en ambos lados de una conexión** y **conexiones de un solo sentido**: ver pendientes en `plan.md`. Se resuelven en la especificación antes de implementar.
- **Punto único de cambio de puertas**: es el riesgo principal de equivalencia. Se mitiga con la prueba de recorrido de código y con la prueba de equivalencia.
- **Ids de sala densos desde 1**: supuesto heredado de la Parte I (`salas` es una lista de tamaño N+1 indexada por id; la posición 0 queda sin usar). Las estructuras de esta capacidad se dimensionan con el mayor id del esqueleto más uno, sin cantidades fijas. Si una cripta nueva rompiera la densidad, afectaría a toda la Parte I, no solo a esta capacidad.
