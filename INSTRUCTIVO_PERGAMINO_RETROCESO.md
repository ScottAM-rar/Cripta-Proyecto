# Instructivo del pergamino de retroceso

## 1. Objetivo

El pergamino de retroceso debe devolver el juego al estado inmediatamente anterior a la última acción del jugador.

La reversión debe incluir los cambios producidos por esa acción y por los eventos posteriores, hasta la siguiente decisión del jugador.

No deben guardarse copias completas del estado. Solo se deben registrar los datos necesarios para invertir cada cambio.

---

## 2. Registrar una acción

Antes del primer cambio producido por una decisión del jugador:

```python
retroceso.nueva_accion()
```

Después se registra uno o más cambios:

```python
retroceso.registrar_cambio([cambio])
```

Una acción puede contener hasta dos `CambioDTO`:

```python
retroceso.registrar_cambio([
    cambio_vida,
    cambio_inventario
])
```

Los efectos posteriores producidos por enemigos, trampas o eventos no deben llamar nuevamente a `nueva_accion()`. Deben registrarse dentro de la acción del jugador que los provocó:

```python
retroceso.registrar_cambio([cambio_enemigo])
```

---

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

## 6. Requisitos de 2.11 y 4.6 todavía pendientes

### Registro automático

Conectar `nueva_accion()` y `registrar_cambio()` al flujo real de `GestorEventos` y `EstadoJuegoLogica`.

Actualmente el historial se llena manualmente.

### Eventos posteriores

Registrar también los cambios producidos entre decisiones del jugador:

- ataques enemigos;
- veneno;
- trampas;
- puertas;
- efectos temporales;
- movimientos automáticos;
- cambios de vida.

### Reloj y agenda de eventos

Registrar información suficiente para restaurar:

- `RelojVirtual.tiempo_actual`;
- eventos retirados del heap;
- eventos nuevos;
- eventos cancelados;
- `secuencia_actual`.

### Rastro y bitácora

Conectar `BitacoraLogica` al historial reversible para restaurar los mensajes o pasos registrados durante el intervalo revertido.

### Puertas y trampas

Crear cambios reversibles para:

- puertas abiertas o cerradas;
- trampas armadas o desarmadas;
- trampas activadas;
- efectos producidos por trampas.

### Exclusión de pergaminos

La reversión no debe modificar la cantidad de pergaminos de retroceso:

- no se revierte el consumo del pergamino usado;
- no se revierte recoger un pergamino;
- no se revierte soltar un pergamino;
- no se registra el uso del pergamino en el historial.

La cantidad final debe ser la cantidad existente al invocar el retroceso menos la unidad consumida.

### Límite de acciones

El historial debe mantener como máximo cinco acciones del jugador. Al superar ese límite, se debe eliminar la acción más antigua junto con todos sus cambios y eventos asociados.

### DTO de resultado

Actualmente `ResultadoEventoDTO` no tiene el campo `cambios`. Mientras ese cambio no se realice, `PergaminoLogica` debe devolver únicamente:

```python
ResultadoEventoDTO(
    exito=True,
    mensaje="..."
)
```
