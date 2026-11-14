# Contrato: texto de las pantallas

Cubre FR-306 a FR-313. Todo es texto plano en español, sin secuencias ANSI; los saltos de línea son `\n`; las pruebas comparan **el texto exacto** que devuelven las funciones de `Controlador/Pantallas.py`. Las marcas `<…>` son datos. Una sección vacía muestra su título y `(ninguno)`; **nunca desaparece**.

## 1. Pantalla de sala (`texto_sala`)

Orden fijo: encabezado de sala → salidas → enemigos → objetos → trampas → estado del jugador → inventario → mensajes.

```text
==================================================
SALA: <nombre> (id <id>)
==================================================

--- SALIDAS ---
  <dirección>  -> <destino>  [<estado>]  costo <costo>
  (ninguna)

--- ENEMIGOS ---
  - <nombre> [<estado>]  vida <actual>/<máx>
  (ninguno)

--- OBJETOS ---
  - <nombre> (id <id_catalogo>)
  (ninguno)

--- TRAMPAS ---
  - <nombre> [daño <n>] <armada|desarmada>
  (ninguna)

--- ESTADO DEL JUGADOR ---
  Vida: <actual>/<máx>
  Tiempo: <t>
  Antorcha: <encendida hasta t=<n>|apagada>

--- INVENTARIO ---
  Objeto actual: <nombre> (id <id>)
  Objeto actual: (inventario vacío)

--- ÚLTIMOS MENSAJES (máx. 20) ---
  <mensaje>
  (sin mensajes)
```

Reglas del formato:

- **Salidas**: una línea por salida, en el orden recibido (el de la sala). `<dirección>` en minúsculas y alineada a 6 columnas; `<destino>` es el nombre de la sala solo si está explorada, si no `sala sin explorar` (FR-219; nunca el id ni el nombre de una sala avistada). `<estado>` ∈ `abierta`, `cerrada`, `cerrada, requiere <llave>`, `sin observar`. `costo` siempre al final.
- **Enemigos**: `<estado>` ∈ `activo`, `dormido`. Un cazador lleva la marca `[cazador]` antes del nombre: `- [cazador] <nombre> [activo] …`. El orden es el recibido.
- **Objetos**: nombre tal como lo entrega el modelo, con la primera letra en mayúscula; si solo llega el id, se limpia el prefijo `itm_`.
- **Trampas**: se conservan los datos que hoy se muestran, en la misma línea fija.
- **Estado del jugador**: tres líneas fijas, en ese orden (vida, tiempo, antorcha).
- **Mensajes**: los últimos 20, del más viejo al más reciente.
- Cada título de sección va precedido de una línea en blanco; no hay línea en blanco al final.

## 2. Resumen de fin de partida (`texto_fin_partida`)

```text
==================================================
FIN DE LA PARTIDA
==================================================
Motivo: <motivo>
Puntaje: <n>
Acciones: <n>
Tiempo: <n>
Vida final: <n>
Salas exploradas: <n>
==================================================
Cripta: <id> (versión <vers>) | Enemigos derrotados: <n>
```

- Los seis rótulos y su orden son fijos (clarificación de FR-307).
- `<motivo>` es el texto del modelo (`El jugador ha muerto`, `El jugador ha llegado a la sala final`); si llega vacío o `None`: `Motivo no informado`.
- `Salas exploradas` sin mapa conocido: `no disponible`.
- La línea final conserva la cripta, la versión y los enemigos derrotados que hoy muestra el resumen.
- Antes del resumen sigue saliendo el aviso del banner: `¡HAS MUERTO! …` o `¡HAS LLEGADO A LA SALA DE SALIDA! …` (texto actual, sin cambios).

## 3. Ayuda (`texto_ayuda`, comando `ayuda`)

```text
COMANDOS DISPONIBLES
  <sintaxis, alineada a 30 columnas>  <descripción>
  …
Los comandos no distinguen mayúsculas de minúsculas.
```

Una fila por entrada de `COMANDOS`, en este orden: movimiento (`norte`, `sur`, `este`, `oeste`), `atacar`, `abrir`, `recoger`, `soltar`, `usar`, `siguiente`, `anterior`, `esperar`, `inventario [peso|valor|nombre]`, `mapa`, `ir a <id de sala>`, `historia <t>`, `historia #k`, `ayuda`, `salir`.
Nota: `cerrar` aparece en el prompt actual pero el mapeo del controlador no lo reconoce, y `guardar` no es un comando (la partida se guarda al salir); por eso ninguno figura en la ayuda (hallazgo T1 del análisis; T004 lo confirma leyendo el controlador).

`ayuda`, `mapa`, `historia …` e `inventario` no consumen tiempo ni cuentan como acción. El comando de ayuda de la fase **post-partida** muestra solo `historia <t>`, `historia #k`, `ayuda` y `salir`.

## 4. Línea de entrada

Se reemplaza el prompt largo actual por:

```text
¿Qué deseas hacer? (escribe 'ayuda' para ver los comandos): 
```

## 5. Mensajes de rechazo y de error (`texto_error`)

Forma única: una línea `<qué pasó> <qué puedes hacer>`. Ejemplos exactos (el catálogo completo se fija al implementar leyendo los `print` actuales del controlador y se lista en la tabla de pruebas):

| Situación | Texto |
|---|---|
| Salida inexistente | `No existe una salida hacia el 'norte'. Mira la lista de SALIDAS y elige una dirección que aparezca.` |
| Puerta cerrada con llave | `La salida hacia el 'este' está cerrada y necesita la llave 'llv_x'. Búscala y usa 'abrir', o elige otra salida.` |
| Comando no reconocido | `No reconozco el comando 'xyz'. Escribe 'ayuda' para ver los comandos.` |
| `ir a` sin número | `El destino de 'ir a' debe ser el número de una sala. Ejemplo: ir a 12.` |
| `historia` mal escrita | `No entendí el parámetro de 'historia'. Usa 'historia <t>' o 'historia #k'.` |
| Inventario vacío | `Tu inventario está vacío. Recoge un objeto con 'recoger'.` |
| Cripta no resoluble (rechazo) | `La cripta <id> no tiene solución, por eso no se abrió la partida. Elige otra cripta, o inicia con --forzar para jugarla de todos modos.` |
| Sin criptas | `No se encontraron criptas disponibles. Revisa la conexión o inicia con --offline si ya descargaste datos.` |
| Número de cripta inválido | `El número no es válido. Ingresa un número entre 1 y <n>.` |

Los mensajes que vienen del modelo (`ValueError` de una acción, etc.) se muestran como `<contexto>: <mensaje del modelo>. <qué hacer>`; el texto del modelo no se reescribe.

## 6. Pruebas de claridad (SC-304 a SC-307)

1. **Orden y secciones**: ≥ 5 situaciones (sala vacía, con enemigos activos y dormidos, con puertas de los tres estados, con trampas, sin mensajes). Las secciones aparecen siempre, en el orden de §1.
2. **Idempotencia**: cada pantalla se construye dos veces con los mismos datos; los textos son iguales carácter por carácter.
3. **Español y texto plano**: ningún texto contiene `\x1b`, tabulaciones ni palabras de la lista (`invalid`, `not found`, `failed`, `unknown`).
4. **Ayuda completa**: cada comando que el controlador reconoce aparece en la ayuda con su sintaxis; cada fila de la ayuda es reconocida.
5. **Rechazos**: cada mensaje del catálogo tiene las dos partes (qué pasó y qué hacer).
6. **Vista sin reglas**: una vista con datos fijos imprime exactamente el texto de la función; la prueba de aislamiento comprueba que `Pantallas.py` no importa `Servicio` ni `Logica`.

## 7. Catálogo completo de mensajes (T004, T005)

Resultado de leer `Controlador/ControladorJuego.py` el 2026-11-13. **Comandos reconocidos hoy** (T004): `norte|sur|este|oeste`, `atacar`, `abrir` (pregunta la dirección), `recoger` (pregunta el número), `usar`, `soltar`, `esperar`, `siguiente`/`sig`, `anterior`/`ant`, `inventario [peso|valor|nombre]`, `mapa`, `ir a <id>`, `historia <t>`, `historia #k`, `salir`. Confirmado: **`cerrar` no se reconoce** (solo aparecía en el texto del prompt) y `guardar` no es un comando, así que ninguno de los dos figura en la ayuda. Se agrega `ayuda`.

Cada fila es una función de `Controlador/Pantallas.py` (`mensaje_<nombre>`); todas se construyen con `texto_error(qué_pasó, qué_hacer)`. «Antes» es el `print` actual.

| Función | Antes | Después |
|---|---|---|
| `sin_criptas` | `No se encontraron criptas disponibles.` | `No se encontraron criptas disponibles. Revisa la conexión o inicia con --offline si ya descargaste datos.` |
| `numero_cripta_invalido(maximo)` | `Número inválido. Debe ser entre 1 y N.` | `El número no es válido. Ingresa un número entre 1 y N.` |
| `no_es_numero` | `Por favor, ingresa un número válido.` | `Eso no es un número. Escribe solo dígitos, por ejemplo 1.` |
| `carga_fallida(error)` | `Error al cargar la partida: E. Se iniciará una nueva.` | `No se pudo cargar la partida: E. Se iniciará una partida nueva; revisa el nombre del archivo si querías cargarla.` |
| `sin_jugador` | `Error: No se pudo obtener el estado del jugador.` | `No se pudo obtener el estado del jugador. Cierra el juego y vuelve a abrirlo.` |
| `historia_sin_parametro` | `Error: Parámetro de historia no reconocido. Usa 'historia <t>' o 'historia #k'.` | `No entendí el parámetro de 'historia'. Usa 'historia <t>' o 'historia #k'.` |
| `historia_no_entero` | `Error: El parámetro debe ser un número entero.` | `El parámetro de 'historia' debe ser un número entero. Ejemplo: historia 200.` |
| `historia_negativo` | `Error: El instante o número de acción no puede ser negativo.` | `El instante o el número de acción no puede ser negativo. Usa 0 o un número mayor.` |
| `historia_accion_cero` | `Error: El número de acción debe ser mayor o igual que 1.` | `El número de acción debe ser 1 o mayor. Ejemplo: historia #1.` |
| `historia_rechazada(error)` | `Error: E` | `No se pudo consultar la historia: E. Prueba con otro instante o número de acción.` |
| `post_partida_desconocido` | `Comando no reconocido. Usa 'historia <t>', 'historia #k' o 'salir'.` | `No reconozco ese comando. Usa 'historia <t>', 'historia #k', 'ayuda' o 'salir'.` |
| `ir_a_destino_invalido` | `El destino debe ser el número de una sala.` | `El destino de 'ir a' debe ser el número de una sala. Ejemplo: ir a 12.` |
| `ir_a_rechazada(error)` | `No se puede viajar: E` | `No se puede viajar: E. Escribe 'mapa' para ver las salas que conoces.` |
| `sin_salida(direccion)` | `No existe una salida hacia el 'D'.` | `No existe una salida hacia el 'D'. Mira la lista de SALIDAS y elige una dirección que aparezca.` |
| `salida_cerrada(direccion)` | `La salida hacia el 'D' está cerrada.` | `La salida hacia el 'D' está cerrada. Usa 'abrir' si tienes con qué, o elige otra salida.` |
| `salida_cerrada_con_llave(direccion, llave)` | `La salida hacia el 'D' está cerrada. Necesitas la llave: 'L'.` | `La salida hacia el 'D' está cerrada y necesita la llave 'L'. Búscala y usa 'abrir', o elige otra salida.` |
| `sin_enemigos` | `No hay enemigos aquí para atacar.` | `No hay enemigos aquí para atacar. Muévete a otra sala o usa 'esperar'.` |
| `enemigo_invalido` | `Número de enemigo inválido.` | `Ese número de enemigo no existe. Elige uno de la lista.` |
| `enemigo_derrotado(nombre)` | `¡N ya está derrotado!` | `N ya está derrotado. Elige otro objetivo o sigue explorando.` |
| `sin_salidas` | `No hay salidas en esta sala.` | `No hay salidas en esta sala. Usa 'mapa' para ver por dónde seguir.` |
| `sin_puertas_cerradas` | `No hay puertas cerradas en esta sala.` | `No hay puertas cerradas en esta sala. Elige una dirección de la lista de SALIDAS.` |
| `direccion_vacia` | `Dirección no válida.` | `No escribiste ninguna dirección. Escribe norte, sur, este u oeste.` |
| `sin_puerta_cerrada(direccion)` | `No hay ninguna puerta cerrada hacia el 'D'.` | `No hay ninguna puerta cerrada hacia el 'D'. Elige una de las direcciones mostradas.` |
| `falta_llave(llave)` | `La puerta está cerrada. Necesitas la llave: 'L' para poder abrirla.` | `La puerta está cerrada y necesitas la llave 'L' para abrirla. Búscala en otras salas.` |
| `sin_objetos` | `No hay objetos aquí para recoger.` | `No hay objetos aquí para recoger. Revisa otras salas.` |
| `objeto_invalido` | `Número de objeto inválido.` | `Ese número de objeto no existe. Elige uno de la lista.` |
| `inventario_vacio` | `Tu inventario está vacío.` | `Tu inventario está vacío. Recoge un objeto con 'recoger'.` |
| `inventario_uso` | `Uso: inventario [peso|valor|nombre]` | `Uso incorrecto de 'inventario'. Escribe 'inventario', 'inventario peso', 'inventario valor' o 'inventario nombre'.` |
| `inventario_rechazado(error)` | `-> E` | `No se puede ordenar el inventario: E. Usa peso, valor o nombre.` |
| `objeto_rechazado(error)` (siguiente/anterior) | `-> E` | `No se puede cambiar de objeto: E. Recoge un objeto con 'recoger'.` |
| `comando_desconocido(texto)` | `Comando no reconocido.` / `Acción no reconocida o comando inválido.` | `No reconozco el comando 'T'. Escribe 'ayuda' para ver los comandos.` |
| `guardado_fallido(error)` | `Error al guardar la partida: E` | `No se pudo guardar la partida: E. Prueba con otro nombre de archivo.` |
| `puntaje_nombre_vacio` | `El nombre no puede estar vacío.` | `El nombre no puede estar vacío. Escribe al menos una letra.` |
| `puntaje_nombre_largo(maximo, largo)` | `El nombre no puede pasar de M caracteres (tiene L).` | `El nombre tiene L caracteres y el máximo es M. Escribe uno más corto.` |
| `puntaje_fallido(error)` | `No se pudo registrar el puntaje: E` | `No se pudo registrar el puntaje: E. La partida terminó igual; puedes seguir consultando la historia.` |
| `puntajes_ilegibles(error)` | `No se pudo leer la tabla de puntajes: E` | `No se pudo leer la tabla de puntajes: E. Sigue jugando; el archivo se revisa al registrar un puntaje.` |
| `mensajes_ilegibles(error)` | `No se pudieron mostrar los mensajes: E` | `No se pudieron mostrar los mensajes: E. El registro completo está en el log de la partida.` |
| `resumen_fallido(error)` | `Error al obtener el resumen: E` | `No se pudo obtener el resumen: E. Revisa el log de la partida.` |
| `cripta_no_resoluble(id)` | `Error: <reporte>` (en `main.py`) | `La cripta ID no tiene solución, por eso no se abrió la partida. Elige otra cripta, o inicia con --forzar para jugarla de todos modos.` |

Los avisos informativos que no son rechazos (`-> Te has movido al siguiente objeto…`, `¡Partida guardada con éxito!`, `Saliendo del juego...`) no cambian.
