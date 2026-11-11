# Capa de lógica de inventario, objetos y retroceso: documentación

Clases documentadas: `InventarioLogica`, `ObjetoLogica`, `NodoCambio`, `RetrocesoLogica`, `PergaminoLogica` y `BitacoraLogica`.

Este documento describe la responsabilidad de cada clase, la estructura de datos utilizada, el flujo de uso y las invariantes que deben conservarse al modificar el proyecto.

---

## 1. Vista general

La lógica documentada se organiza en tres partes:

```text
JugadorDTO
  |
  +--> InventarioLogica ---------> NodoInventario
  |       |
  |       +--> ObjetoLogica ------> PergaminoLogica
  |                                  |
  |                                  +--> RetrocesoLogica --> NodoCambio --> CambioDTO
  |
  +--> BitacoraLogica
```

- `InventarioLogica` mantiene los objetos del jugador en una lista doblemente enlazada y administra el nodo `actual`.
- `ObjetoLogica` aplica el comportamiento de cada tipo de objeto y registra los cambios que pueden deshacerse.
- `RetrocesoLogica` conserva un historial limitado de 5 acciones agrupadas.
- `NodoCambio` es el nodo de la lista doble enlazada `RetrocesoLogica` que almacena un grupo de `CambioDTO`.
- `PergaminoLogica` interpreta los cambios guardados en `RetrocesoLogica` en orden inverso y restaura hasta la accion anterior.
- `BitacoraLogica` mantiene los resultados de eventos en una cola enlazada con capacidad de 20 elementos.

Las clases de retroceso comparten el contrato de `CambioDTO`: cada cambio debe indicar el tipo de acción, el objeto afectado y los valores necesarios para restaurarlo.

---

## 2. Guía rápida

### 2.1 Crear y recorrer un inventario

```python
inventario = InventarioLogica(capacidad_maxima=10)
inventario.agregar_objeto(objeto)

actual = inventario.mostrar_objeto_actual()
inventario.siguiente_objeto()
inventario.anterior_objeto()
```

El inventario empieza con `cabeza`, `cola` y `actual` apuntando al primer nodo. Al eliminar o soltar el objeto actual, el cursor vuelve a `cabeza`.

### 2.2 Usar objetos

`ObjetoLogica.usar_objeto(objeto)` verifica que el objeto esté en el inventario y decide su comportamiento mediante `match`:

- `Pocion`: la consume y aplica curación o modificación de velocidad (En casos de pociones de velocidad).
- `Antidoto`: la consume y elimina el veneno.
- `Antorcha`: la consume, enciende la antorcha y agenda su apagado.
- `Arma` o `Armadura`: equipa el objeto actual al jugador y actualiza sus atributo de daño o defensa.
- `PergaminoRetroceso`: consume el pergamino solo si existe historial y ejecuta el retroceso hasta la ultima accion realizada.
- `Llave`: no se usa directamente; debe utilizarse en una puerta.

### 2.3 Registrar y deshacer una acción

```python
marcador = retroceso.iniciar_accion()
retroceso.registrar_cambio([
    CambioDTO("ACTUALIZAR_VIDA", jugador, valor_anterior=100)
])

pergamino_logica.usar_pergamino()
```

Una acción puede contener varios nodos de cambio. El pergamino obtiene el último grupo, aplica sus cambios desde el último hasta el primero y elimina ese grupo del historial.

### 2.4 Registrar resultados en la bitácora

```python
bitacora.agregar_evento(resultado)
mensajes = bitacora.obtener_eventos()
```

La bitácora conserva los 20 resultados más recientes en orden FIFO.

---

## 3. `InventarioLogica`

Archivo: `Logica/InventarioLogica.py`.

### Responsabilidad

Administra una lista doblemente enlazada de objetos. Mantiene tres referencias principales:

| Atributo | Significado |
|---|---|
| `cabeza` | Primer nodo del inventario; también representa el primer objeto equipado. |
| `cola` | Último nodo del inventario. |
| `actual` | Cursor utilizado por la navegación normal del jugador. |
| `cantidad_actual` | Número de nodos almacenados. |
| `capacidad_maxima` | Límite de objetos permitidos. |

### Operaciones principales

- `agregar_objeto(objeto)`: inserta al final. Lanza `ValueError` si se alcanzó la capacidad.
- `eliminar_objeto_utilizado(objeto)`: busca por identidad (`is`), elimina el nodo y reinicia `actual` en la cabeza.
- `siguiente_objeto()` y `anterior_objeto()`: mueven el cursor si existe un vecino y devuelven `True`; devuelven `False` en los extremos.
- `soltar_objeto_actual()`: elimina el nodo apuntado por `actual` y devuelve el objeto eliminado.
- `mostrar_objeto_actual()`: devuelve el objeto del cursor.
- `equipar_objeto_actual()`: mueve el objeto actual a una de las dos primeras posiciones. Si ya está en ellas, no cambia la lista.
- `mostrar_equipado_1()` y `mostrar_equipado_2()`: validan que el primer o segundo objeto sea `Arma` o `Armadura` y si es, lo devuelve para mostrarlo.
- `obtener_vista_ordenada(criterio)`: crea una vista ordenada por `peso`, `valor` o `nombre` sin alterar los enlaces reales.

### Operaciones para el funcionamiento del retroceso

- `buscar_objeto(objeto)` e `indice_de_objeto(objeto)`: realizan búsquedas lineales por identidad.
- `mover_objeto_equipado_a_su_indice_anterior(indice, objeto)`: saca un objeto equipado y lo devuelve a su posición original.
- `eliminar_objeto_por_retroceso(objeto)`: elimina un objeto sin depender de `actual`.
- `insertar_en_indice_por_retroceso(indice, objeto)`: crea un nodo y lo inserta en una posición concreta.
- `equipar_objeto_por_retroceso(objeto)`: mueve un objeto al frente para restaurar un equipamiento.

Estas operaciones pueden modificar `cabeza`, `cola` y `cantidad_actual`, pero deben conservar siempre los enlaces anterior/siguiente.

### Invariantes

1. Si el inventario está vacío, `cabeza`, `cola` y `actual` son `None` y `cantidad_actual` vale 0.
2. Si no está vacío, `cabeza.anterior` y `cola.siguiente` son `None`.
3. Cada enlace hacia adelante debe tener su enlace inverso correspondiente.
4. `cantidad_actual` debe coincidir con el número real de nodos.
5. Equipar no cambia la cantidad de objetos.
6. La vista ordenada no cambia el orden físico de la lista.

### Complejidad

La navegación entre vecinos y la inserción al final son operaciones $O(1)$. Buscar, eliminar por objeto, obtener un índice, ordenar una vista y mover a una posición arbitraria requieren recorrer la lista y son $O(n)$, sin contar el algoritmo de ordenamiento empleado.

---

## 4. `ObjetoLogica`

Archivo: `Logica/ObjetoLogica.py`.

### Responsabilidad

Es el coordinador del uso de objetos del jugador. Recibe un `JugadorDTO` y una `PergaminoLogica`. Antes de actuar verifica que el objeto exista en el inventario.

### Flujo de `usar_objeto`

1. Busca el objeto y guarda su índice original.
2. Ejecuta el comportamiento según el tipo concreto.
3. Construye uno o varios `CambioDTO` con los valores anteriores necesarios.
4. Registra el grupo en `RetrocesoLogica`, salvo cuando el pergamino consume el historial.
5. Devuelve un `ResultadoEventoDTO` con éxito, mensaje y, cuando corresponde, un evento futuro.

Las acciones compuestas, como consumir una poción y actualizar la vida, se registran como varios cambios dentro de una misma acción lógica. Así el pergamino deshace la acción completa, no solo una parte.

### Métodos auxiliares

- `_consumir`: elimina el objeto usado del inventario.
- `_aplicar_pocion`: aplica curación limitada por `vida_max` o un modificador de velocidad.
- `_revertir_modificador_velocidad`: restaura el modificador cuando corresponde a un evento programado.
- `_aplicar_antidoto`: establece `veneno` en `False`.
- `_usar_antorcha` y `_apagar_antorcha`: controlan el estado de la antorcha y su evento futuro.
- `_equipar`: mueve el objeto actual y actualiza `jugador.arma` o `jugador.armadura`.

### Regla de cursor

El método `_equipar` exige que el objeto recibido sea exactamente el objeto del nodo `actual`. La selección de un objeto y el movimiento del cursor son responsabilidades del flujo que llama a `ObjetoLogica`.

---

## 5. `NodoCambio`

Archivo: `Logica/NodoCambio.py`.

### Responsabilidad

Representa un nodo de la lista doble de retroceso. Su atributo `objeto` contiene una lista no vacía de `CambioDTO`, porque una acción del juego puede modificar varios estados.

| Atributo | Significado |
|---|---|
| `objeto` | Lista de cambios que forman el nodo. |
| `es_accion` | Marca el inicio de una acción del jugador. |
| `anterior` | Nodo previo. |
| `siguiente` | Nodo siguiente. |

El constructor rechaza una lista vacía mediante `ValueError`. `NodoCambio` no aplica cambios por sí mismo; solo proporciona almacenamiento enlazado para `RetrocesoLogica`.

---

## 6. `RetrocesoLogica`

Archivo: `Logica/RetrocesoLogica.py`.

### Responsabilidad

Implementa el historial de cambios como un singleton y una lista doblemente enlazada. El historial tiene como máximo cinco acciones (`MAX_HISTORIAL = 5`), aunque cada acción puede ocupar varios nodos de cambio.

### Contadores

- `cantidad_actual`: cantidad total de nodos almacenados, incluyendo marcadores y cambios.
- `cantidad_acciones`: cantidad de acciones del jugador que todavía pueden deshacerse.
- `tiempo_evento`: tiempo asociado a la acción que se está registrando.
- `suspensiones`: número de bloques `sin_registro` activos.

No se deben confundir `cantidad_actual` y `cantidad_acciones`: el primero cuenta nodos y el segundo grupos reversibles.

### Métodos principales

- `iniciar_accion(tiempo_ejecucion=None)`: crea un `NodoCambio` marcador con `es_accion=True`.
- `registrar_cambio(cambio, tiempo_ejecucion=None)`: agrega un grupo de cambios a la acción abierta. Si no existe una acción abierta, ignora el registro.
- `obtener_cambios_retroceso()`: extrae nodos desde la cola hasta encontrar el marcador de la última acción.
- `pop()`: elimina el último nodo.
- `descartar_accion(marcador)`: elimina una acción incompleta desde la cola.
- `_eliminar_accion_mas_antigua()`: elimina el marcador más antiguo y todos sus cambios cuando se supera el máximo.
- `sin_registro()`: contexto para cargar datos o crear eventos sin añadirlos al historial.
- `reiniciar()`: restablece el singleton para una nueva partida o prueba.

### Tiempo y agenda

`registrar_encolado` y `registrar_desencolado` guardan los cambios de la agenda del reloj. Al revertir, `PergaminoLogica` puede quitar eventos creados o reinsertar eventos desencolados. El tiempo se conserva en cada `CambioDTO` mediante `tiempo_ejecucion`.

### Invariante de acciones

Cada grupo reversible comienza con un marcador `es_accion=True`. Los cambios posteriores pertenecen a ese grupo hasta el siguiente marcador. La extracción se hace desde la cola, por lo que los cambios se revierten en orden LIFO.

---

## 7. `PergaminoLogica`

Archivo: `Logica/PergaminoLogica.py`.

### Responsabilidad

Aplica el retroceso solicitado por el jugador. Recibe el historial y la lista de salas para poder restaurar objetos y enemigos en su ubicación anterior.

`usar_pergamino()` devuelve un resultado fallido si no hay acciones. En caso contrario obtiene el último grupo y llama a `aplicar_cambios`.

### Orden de restauración

`aplicar_cambios` recorre los nodos obtenidos y, dentro de cada nodo, recorre los `CambioDTO` en orden inverso. Esto es esencial para acciones compuestas: primero se deshace el efecto más reciente y luego se restaura el estado que lo precedía.

### Tipos de cambio soportados

| Tipo | Restauración |
|---|---|
| `ACTUALIZAR_VIDA` | Recupera `valor_anterior` en `vida_actual`. |
| `MOVER` | Devuelve jugador o enemigo a la sala anterior; mueve enemigos entre listas. |
| `RECOGER_OBJETO` | Quita el objeto del inventario y lo devuelve a la sala. |
| `SOLTAR_OBJETO` | Quita el objeto de la sala y lo inserta en su índice original. |
| `EQUIPAR_OBJETO` | Restaura el equipo anterior y recoloca el objeto equipado. |
| `DESEQUIPAR_OBJETO` | Restaura el equipo anterior, inserta el objeto y lo equipa. |
| `USAR_OBJETO` | Devuelve al inventario un objeto consumido. |
| `REVERTIR_MODIFICADOR_VELOCIDAD` | Recupera el modificador anterior. |
| `USAR_ANTORCHA` / `APAGAR_ANTORCHA` | Recupera el estado anterior de la antorcha. |
| `APLICAR_ANTIDOTO` | Recupera el estado anterior del veneno. |
| `CAMBIAR_PUERTA` / `CAMBIAR_TRAMPA` | Restaura el estado previo. |
| `INICIO_ACCION` | Restaura tiempo y secuencia del reloj. |
| `EVENTO_ENCOLADO` / `EVENTO_DESENCOLADO` | Quita o reinserta eventos de la agenda. |
| `ACTUALIZAR_PUNTAJE` | Recupera el puntaje anterior. |
| `ENEMIGOS_ELIMINADOS` | Recupera el contador anterior. |
| `ULTIMO_PASO` | Recupera la marca temporal anterior de la sala. |
| `BITACORA_AGREGADA` | Quita el resultado agregado y recupera el descartado, si existía. |

El uso de un `PergaminoRetroceso` no se revierte: el historial que permitió ejecutar el pergamino ya fue consumido y no debe reconstruirse recursivamente.

Un tipo de cambio desconocido provoca `ValueError`, lo cual evita que el sistema informe un retroceso aparentemente exitoso cuando no sabe restaurar una acción.

---

## 8. `BitacoraLogica`

Archivo: `Logica/BitacoraLogica.py`.

### Responsabilidad

Almacena resultados de eventos para mostrar mensajes al jugador. Usa una cola FIFO implementada con nodos enlazados simples.

- `agregar_evento(resultado)`: agrega al final y devuelve el resultado descartado cuando se supera la capacidad.
- `quitar_resultado(resultado)`: elimina por identidad y devuelve `True` si lo encontró.
- `poner_al_frente(resultado)`: reinsertar un resultado al inicio, útil para el retroceso.
- `obtener_eventos()`: devuelve una lista desde el más antiguo al más reciente.
- `imprimir_mensajes()`: imprime los mensajes en ese mismo orden.

Solo acepta instancias de `ResultadoEventoDTO`. La capacidad es 20; al agregar el elemento número 21, se descarta el más antiguo.

### Invariantes

1. `frente` es el resultado más antiguo y `final` el más reciente.
2. Si la bitácora está vacía, ambos punteros son `None`.
3. `contador` coincide con la cantidad de nodos.
4. `final.siguiente` siempre es `None`.

---

## 9. Flujo completo

```text
Jugador selecciona objeto
        |
        v
ObjetoLogica.usar_objeto
        |
        +--> InventarioLogica elimina/equipa el objeto
        +--> se actualizan jugador, sala o reloj
        +--> se crean CambioDTO
        +--> RetrocesoLogica.registrar_cambio
        +--> BitacoraLogica agrega el resultado
        |
Jugador usa pergamino
        |
        v
PergaminoLogica.usar_pergamino
        |
        +--> RetrocesoLogica extrae la última acción
        +--> se aplican cambios en orden inverso
        +--> inventario, salas, reloj y bitácora vuelven al estado anterior
```

La prueba más fuerte de este flujo es `test_retroceso_flujo.py`, que compara el estado completo antes y después de varias acciones. Las pruebas unitarias de `test_pergamino_logica.py` y `test_bitacora_logica.py` cubren restauraciones específicas.

---