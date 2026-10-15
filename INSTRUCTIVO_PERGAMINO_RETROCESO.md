# Instructivo del pergamino de retroceso

## 1. Objetivo

El pergamino de retroceso debe devolver el juego al estado inmediatamente anterior a la última acción del jugador.

La reversión debe incluir los cambios producidos por esa acción y por los eventos posteriores, hasta la siguiente decisión del jugador.

No deben guardarse copias completas del estado. Solo se deben registrar los datos necesarios para invertir cada cambio.

---

## 2. Registrar una acción

El historial se divide en grupos. Un grupo empieza con un nodo marcador (`es_accion=True`) creado cuando `GestorEventos` procesa un evento del jugador, y contiene todo lo que ocurre después hasta el siguiente marcador: cambios del jugador, efectos de enemigos, trampas, puertas, pociones y antorchas.

`GestorEventos.procesar_evento` abre el grupo automáticamente con `retroceso.iniciar_accion(...)`; el marcador guarda `tiempo_actual` y `secuencia_actual` del reloj. Las acciones fallidas o sin efecto del jugador (incluido esperar) también abren grupo. Usar un pergamino no abre grupo.

Las operaciones sobre la agenda del `RelojVirtual` (`encolar`, `desencolar`) se registran solas como `EVENTO_ENCOLADO` / `EVENTO_DESENCOLADO`, por lo que al retroceder se reconstruye la agenda: los enemigos, trampas, puertas, pociones y antorchas vuelven a tener sus eventos pendientes.

Los eventos creados al cargar una sala se encolan dentro de `retroceso.sin_registro()` para que no se deshagan.

Cada uso del pergamino deshace un grupo completo (máximo `MAX_HISTORIAL` = 5) y no se consume si no hay historial.

También se revierten reloj, puntaje, enemigos eliminados, último paso y bitácora (`ACTUALIZAR_PUNTAJE`, `ENEMIGOS_ELIMINADOS`, `ULTIMO_PASO`, `BITACORA_AGREGADA`).

## 3. Estructura de `CambioDTO`

```python
CambioDTO(
    tipo_accion="...",
    objeto_afectado=..., 
    valor_anterior=..., 
    valor_nuevo=..., 
    elemento=..., 
    indice=...
)
```

Los campos utilizados dependen del caso.

---

## 4. Casos implementados

### 4.1 `ACTUALIZAR_VIDA`

Se registra cuando cambia la vida de un jugador o enemigo.

```python
cambio = CambioDTO(
    tipo_accion="ACTUALIZAR_VIDA",
    objeto_afectado=jugador,
    valor_anterior=100,
    valor_nuevo=80
)
```

Campos requeridos:

- `objeto_afectado`: actor cuya vida cambió.
- `valor_anterior`: vida antes del cambio.
- `valor_nuevo`: vida después del cambio.

La reversión restaura `valor_anterior`.

---

### 4.2 `MOVER`

Para un jugador:

```python
cambio = CambioDTO(
    tipo_accion="MOVER",
    objeto_afectado=jugador,
    valor_anterior=sala_anterior,
    valor_nuevo=sala_nueva
)
```

Para un enemigo:

```python
cambio = CambioDTO(
    tipo_accion="MOVER",
    objeto_afectado=enemigo,
    valor_anterior=sala_anterior,
    valor_nuevo=sala_nueva
)
```

Campos requeridos:

- `objeto_afectado`: jugador o enemigo.
- `valor_anterior`: instancia de `SalaDTO` de origen.
- `valor_nuevo`: instancia de `SalaDTO` de destino.

Para un enemigo, al registrar el cambio debe estar en `valor_nuevo.enemigos` y no en `valor_anterior.enemigos`.

---

### 4.3 `RECOGER_OBJETO`

```python
cambio = CambioDTO(
    tipo_accion="RECOGER_OBJETO",
    objeto_afectado=jugador,
    valor_anterior=sala,
    elemento=objeto
)
```

Estado esperado al registrar:

- el objeto ya no está en la sala;
- el objeto ya está en el inventario.

La reversión elimina el objeto del inventario y lo devuelve a `sala.objetos`.

Los objetos `PergaminoRetroceso` deben excluirse de esta reversión según la especificación del proyecto.

---

### 4.4 `SOLTAR_OBJETO`

```python
cambio = CambioDTO(
    tipo_accion="SOLTAR_OBJETO",
    objeto_afectado=jugador,
    valor_anterior=sala,
    elemento=objeto,
    indice=indice_original
)
```

Estado esperado al registrar:

- el objeto ya está en la sala;
- el objeto ya no está en el inventario.

La reversión elimina el objeto de la sala y lo devuelve al inventario.

El `case` actual utiliza `agregar_objeto()`, por lo que el objeto vuelve al final del inventario. Para restaurar exactamente el orden anterior, se debe utilizar `indice` con una función de inserción por retroceso.

Los objetos `PergaminoRetroceso` deben excluirse de esta reversión.

---

### 4.5 `EQUIPAR_OBJETO`

```python
cambio = CambioDTO(
    tipo_accion="EQUIPAR_OBJETO",
    objeto_afectado=jugador,
    valor_anterior=arma_anterior,
    valor_nuevo=arma_nueva,
    elemento=arma_nueva,
    indice=indice_original
)
```

Para armaduras, `elemento` debe ser una instancia de `Armadura`.

Campos requeridos:

- `elemento`: objeto que se equipó;
- `valor_anterior`: objeto equipado anteriormente, o `None` si era el primero;
- `indice`: posición original del objeto antes de equiparse.

La reversión restaura el objeto equipado anteriormente y mueve el nuevo objeto a su índice original.

---

### 4.6 `DESEQUIPAR_OBJETO`

```python
cambio = CambioDTO(
    tipo_accion="DESEQUIPAR_OBJETO",
    objeto_afectado=jugador,
    valor_anterior=objeto_desequipado,
    elemento=objeto_desequipado,
    indice=indice_original
)
```

Campos requeridos:

- `valor_anterior`: objeto que estaba equipado;
- `elemento`: el mismo objeto;
- `indice`: posición que tenía en el inventario.

La reversión devuelve el objeto a su posición y vuelve a equiparlo.

`valor_anterior` no debe ser `None`, porque se utiliza para volver a equipar el objeto.

---

### 4.7 `USAR_OBJETO`

```python
cambio = CambioDTO(
    tipo_accion="USAR_OBJETO",
    objeto_afectado=jugador,
    elemento=pocion,
    indice=indice_original
)
```

Estado esperado al registrar:

- el objeto ya fue usado;
- el objeto ya fue eliminado del inventario.

La reversión debe utilizar `insertar_en_indice_por_retroceso()`, porque el objeto ya no existe en la lista y debe crearse un nuevo nodo.

El uso de un `PergaminoRetroceso` no debe registrarse como un cambio reversible.

---

### 4.8 `REVERTIR_MODIFICADOR_VELOCIDAD`

```python
cambio = CambioDTO(
    tipo_accion="REVERTIR_MODIFICADOR_VELOCIDAD",
    objeto_afectado=jugador,
    valor_anterior=modificador_anterior,
    valor_nuevo=modificador_actual
)
```

`valor_anterior` debe contener el valor completo anterior de `jugador.modificador_velocidad`.

---

### 4.9 `USAR_ANTORCHA`

```python
cambio = CambioDTO(
    tipo_accion="USAR_ANTORCHA",
    objeto_afectado=jugador,
    valor_anterior=False,
    valor_nuevo=True
)
```

La reversión restaura `antorcha_encendida` a `False`.

---

### 4.10 `APAGAR_ANTORCHA`

```python
cambio = CambioDTO(
    tipo_accion="APAGAR_ANTORCHA",
    objeto_afectado=jugador,
    valor_anterior=True,
    valor_nuevo=False
)
```

La reversión restaura `antorcha_encendida` a `True`.

---

### 4.11 `APLICAR_ANTIDOTO`

```python
cambio = CambioDTO(
    tipo_accion="APLICAR_ANTIDOTO",
    objeto_afectado=jugador,
    valor_anterior=True,
    valor_nuevo=False
)
```

La reversión restaura `jugador.veneno` a `True`.

---

## 5. Uso del pergamino

La llamada principal es:

```python
resultado = pergamino_logica.usar_pergamino()
```

El flujo debe ser:

1. comprobar si existe una acción para deshacer;
2. obtener la última acción completa;
3. revertir sus cambios en orden inverso;
4. eliminar esa acción del historial;
5. devolver un resultado exitoso.

Si no existe historial, el pergamino no debe consumirse.

El uso del pergamino no debe avanzar el reloj ni registrarse como una acción del jugador.

---

## 6. Estado

Los puntos antes pendientes (registro automático, eventos posteriores, reloj y agenda, rastro y bitácora, puertas y trampas, exclusión de pergaminos, límite de acciones) quedaron implementados. Ver `test_retroceso_flujo.py`.
