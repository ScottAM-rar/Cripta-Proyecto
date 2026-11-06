# Investigación (Fase 0): Recorrido por niveles

No quedan marcadores `NEEDS CLARIFICATION`. Todo lo de este documento es de **cómo**; las reglas están solo en `spec.md`.

## 1. Qué se reutiliza del repositorio

| Pieza | Dónde | Uso |
|---|---|---|
| Aristas salientes por sala | `Logica/MapaCripta.py` (capacidad 001) | Entrada del recorrido. Lista por id de sala; cada arista trae destino y dirección |
| Tamaño del esqueleto | `MapaCripta.tamano` (mayor id + 1) | Dimensiona las listas de marcas y niveles |
| `ordenar_adaptativo` | `Logica/ordenamiento.py` | Ordena cada nivel por id. Estable; inserción hasta 15 elementos, mezcla por encima |
| `MonticuloMinimo` | `Logica/MonticuloMinimo.py` | Solo en la alternativa de orden por montículo (§4), medida en el bench |
| Generadores de criptas | `tests_labs/cripta_sintetica.py` | Criptas deterministas por semilla para pruebas y `--bench` |
| `medir`, `anotar`, `verificar` | `bench/medicion.py` | Mediciones y comprobaciones previas |

**Hallazgo**: `MapaCripta` solo guarda el estado **inicial** de las puertas y lee el actual de las salas cargadas con `esta_abierta`. El recorrido no lo necesita por defecto (valen todas las salidas, FR-507): si quien lo pide quiere puertas, pasa una función que llama a `esta_abierta`.

**Cambio mínimo a `MapaCripta`**: hoy no distingue «sala sin salidas» de «id que no existe», y FR-512 exige rechazar un origen inexistente. Se agrega una lista de existencia (una posición por id). No cambia nada de lo que ya hace.

## 2. Estructuras elegidas

### Visitados: marca de época por id (decisión pedida)

Dos listas de tamaño `MapaCripta.tamano`: `marca` (época en la que se visitó la sala) y `nivel` (nivel en que se visitó). Una sala está visitada en este recorrido si `marca[sala] == época`. Cada recorrido incrementa la época, así que **reiniciar es O(1)** y el costo no depende de N (FR-510).

| Alternativa | Por qué se descarta (razón concreta) |
|---|---|
| `dict` o `set` de visitados | Prohibido por el principio I |
| Lista de visitados limpiada en cada recorrido | Limpiar N posiciones cuesta O(N) en cada llamada: un recorrido de 2 niveles en 40 000 salas pagaría 40 000 escrituras. Incumple FR-510 |
| Buscar con `in` en la lista de salas ya visitadas | Cada comprobación cuesta O(V): el recorrido sería O(V²). Es lo que hace hoy `ServicioCripta.salas_vecinas` |
| Crear listas nuevas por recorrido | Asignar N posiciones cuesta O(N) por llamada, igual que limpiar |

**Costo de esta decisión**: las dos listas ocupan O(N) memoria permanente por mapa, aunque se recorran pocas salas. Es aceptable: ya existen del mismo orden en `MapaCripta` (aristas salientes y entrantes).

### Cola: circular sobre una lista que crece al llenarse (decisión pedida)

Una lista de capacidad fija con índices de cabeza y de cola que giran. Al llenarse, la capacidad se duplica y los elementos se copian en orden desde la cabeza. Operaciones: `agregar`, `sacar`, `vacia`, `vaciar`, longitud.

| Alternativa | Complejidad | Razón concreta para compararla o descartarla |
|---|---|---|
| **Cola circular (elegida)** | agregar/sacar O(1) amortizado | Memoria acotada por la frontera más ancha; reutilizable entre recorridos sin reasignar |
| `list` con `pop(0)` | sacar O(longitud de la cola) | Cada `pop(0)` desplaza todos los elementos restantes. Con una frontera de a elementos, sacar V salas cuesta O(V·a). En una cripta de frontera ancha (árbol) crece como V². Se mide en el bench |
| `list` + índice de cabeza que solo avanza | O(1) | Nunca libera lo ya sacado: la memoria crece con V aunque la frontera sea chica. Más simple; se mide |
| Dos listas por nivel (actual y siguiente, se intercambian) | O(1) | No necesita cola. Ver §3: es la alternativa seria |
| `collections.deque` | O(1) | Prohibido por el principio I |

### Resultado

Dos listas en paralelo: `salas` y `niveles`, en el orden de visita. Una `list` de enteros por campo evita crear un objeto por sala visitada.

## 3. La cola y el orden por nivel: una observación honesta

Para cumplir FR-502 (menor id dentro del nivel) hay que **ordenar cada nivel antes de procesarlo**. Eso implica que, mientras se procesa el nivel k, los descubrimientos del nivel k+1 se acumulan **aparte** y solo se ordenan y encolan cuando termina el nivel k. Por eso la cola contiene en cada momento **un solo nivel**: es, en la práctica, el «nivel actual», y la lista auxiliar es el «nivel siguiente».

Esto es exactamente lo que haría un recorrido con dos listas que se intercambian, sin cola. El plan mantiene la cola circular porque es lo pedido y porque da una estructura general reutilizable, pero:

- El bench mide la cola circular **frente a** las dos listas por nivel, y frente a `pop(0)` y al índice de cabeza.
- **Si las dos listas ganan con claridad, se cambia la decisión y se documenta el antes y el después** (principio VII y `DECISIONES.md`). La cola circular quedaría como estructura de apoyo.
- El resultado es el mismo en todas las variantes; lo que cambia es el costo y la cantidad de piezas.

## 4. Orden dentro de cada nivel

**Por qué hace falta ordenar.** El orden en que se descubren las salas de un nivel sigue el orden de sus **padres**, no el de sus ids. Ejemplo: el origen 1 tiene dos salidas, hacia la 5 y hacia la 3; la 3 lleva a la 9 y la 5 lleva a la 4. El nivel 1 ordenado por id es (3, 5). Al procesarlo en ese orden se descubre primero el hijo de la 3 (la 9) y luego el de la 5 (la 4): el nivel 2 sale como (9, 4), pero FR-502 pide (4, 9). Ni procesar los padres en orden de id ni tener las salidas de cada sala ordenadas por destino lo arregla, porque el desorden aparece **entre** hijos de padres distintos.

| Alternativa | Complejidad | Decisión |
|---|---|---|
| **`ordenar_adaptativo` por nivel (elegida)** | O(m²) si m ≤ 15 (inserción), O(m log m) por encima (mezcla) | Es el ordenamiento propio del repositorio, estable, que ya elige algoritmo según tamaño (medido en `bench/ordenamiento.py`). Los niveles de una cripta son angostos (cada sala tiene a lo sumo 4 salidas) y la inserción es la mejor para ellos |
| `sorted()` / `list.sort()` | O(m log m) | Funciona, pero la convención del repositorio es no usarlos para ordenar lo evaluado. La constitución no los prohíbe de forma expresa; se descartan por coherencia con `bench/ordenamiento.py` y porque el ordenamiento propio ya cubre el caso |
| Montículo con clave `(nivel, id)` (`MonticuloMinimo`) | O(V log V) en total | **Alternativa seria**: la salida sale directamente en el orden pedido, sin cola ni ordenar por nivel. Cuesta O(log V) por sala frente a O(log a) del orden por nivel, y con a pequeño el orden por nivel gana. Se mide en el bench |
| Inserción ordenada en la cola con búsqueda binaria | O(m) por inserción | Necesitaría `bisect` (prohibido) o inserción lineal, que da O(m²) por nivel |
| Ordenar con clave `(nivel, id)` al final | O(V log V) | Obliga a conocer todo el recorrido antes de empezar: con un límite de niveles no ahorra el descubrimiento más allá de lo necesario y hace el recorrido no incremental |

**Corrección del ordenamiento**: la propiedad que se prueba es que dentro de cada nivel los ids salen estrictamente crecientes y que el conjunto de cada nivel coincide con el de una referencia ingenua.

## 5. Límite de niveles y costo proporcional

Las salidas de una sala con nivel igual al límite **no se examinan**. Así el costo es proporcional a las salas y salidas efectivamente visitadas (FR-510): con límite 0 solo se toca el origen.

Validación (FR-504): el límite debe ser un entero no booleano mayor o igual que 0, o ausente. Cualquier otro valor se rechaza con `ValueError` y un mensaje que dice cuál fue el valor.

## 6. Criterio de transitabilidad

`recorrer(origen, limite=None, transitable=None)`. `transitable` es una función que recibe la arista (con origen, dirección y destino) y devuelve verdadero o falso. Con `None`, todas son transitables. Se evalúa **una vez por arista examinada**, en el momento de examinarla.

Consecuencia para el determinismo (FR-509): si el criterio lee estado que cambia (por ejemplo puertas), el resultado depende de ese estado en el instante de la llamada. Es responsabilidad de quien pide el recorrido pasar un criterio que dé lo mismo en dos llamadas iguales; el recorrido en sí no introduce ninguna otra fuente de variación.

## 7. Casos límite que el diseño resuelve

| Caso | Tratamiento |
|---|---|
| Origen inexistente (FR-512) | `ValueError` antes de recorrer; se comprueba con la lista de existencia de `MapaCripta` |
| Salida hacia una sala que no existe en el esqueleto | Se ignora: no hay sala que visitar |
| Salida de una sala a sí misma | La sala ya está marcada: se ignora |
| Varias salidas hacia la misma sala | La primera la marca; las demás encuentran la marca |
| Origen dentro de un ciclo | El origen se marca antes de empezar: aparece una vez, al principio |
| Conexión de un solo sentido | Solo existe la arista saliente en un sentido; no se inventa la inversa |
| Origen sin salidas o con ninguna transitable | Recorrido de una sola sala (FR-508) |

## 8. Mediciones planificadas (principio VII)

Bloque `recorrido` de `--bench`, con criptas sintéticas deterministas por semilla.

| Sección | Qué compara | Criterio |
|---|---|---|
| A. Acotado frente a sin límite al crecer la cripta | Recorrido de 2 y 5 niveles frente a sin límite, en rejillas de 400, 4 900 y 40 000 salas, mismo origen central | SC-004: el acotado de 2 niveles en 40 000 salas toma a lo sumo el doble que en 400; el sin límite crece con N. Se informa también cuántas salas se visitaron |
| B. Cola circular frente a la alternativa descartada | Cola circular · `pop(0)` · índice de cabeza · dos listas por nivel, sobre la misma cripta y la misma orden | Todas deben dar el mismo recorrido (verificación previa). Se informa el tiempo de cada una |
| C. Dos formas de cripta | B se repite en **rejilla** (frontera angosta) y en **árbol de ramificación 3** de 29 524 salas (frontera ancha: el último nivel tiene 19 683) | Muestra dónde `pop(0)` se degrada y dónde da igual |
| D. Orden dentro del nivel | `ordenar_adaptativo` por nivel frente a montículo `(nivel, id)` | Informa la ganancia; si el montículo gana, se cambia |
| E. Referencia actual | `ServicioCripta.salas_vecinas` (con `deque` y `in` lineal) frente al recorrido nuevo, mismo origen y límite | Solo informativa: es lo que se reemplazará después |
| F. Equivalencia | Recorrido frente a referencia ingenua en criptas aleatorias con ciclos, caminos paralelos, un solo sentido y criterios de transitabilidad | 0 diferencias en secuencia y niveles |

**Plan frente a lo medido**: si B, C o D contradicen una decisión, se cambia el código y se documenta el antes y el después en `DECISIONES.md`.

## 9. Riesgos

- **SC-004 depende del hardware y de Python**: las listas de 40 000 posiciones caben en caché, pero una medición ruidosa puede dar 2,1×. Si pasa, se corrige `spec.md` primero y luego el criterio del bench.
- **Cola y orden por nivel solapados**: ver §3. Es un riesgo de diseño asumido y medido.
- **Ids densos desde 1**: supuesto heredado de la Parte I y de la capacidad 001. Las listas tienen `mayor id + 1` posiciones; la posición 0 no se usa.
