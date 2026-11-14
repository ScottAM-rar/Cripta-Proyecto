# Investigación y decisiones: Arranque verificado y pantallas de consola claras

Cada decisión indica la elegida, al menos dos alternativas con su complejidad y módulos afectados, y por qué se descartan. «n» es la cantidad de líneas del texto (enemigos, objetos, salidas).

## Estado actual (lo que ya existe)

- `EstadoJuegoServicio.verificar(cripta_id)` devuelve un `ResultadoVerificacion` (`resoluble` en `True`, `False` o `None` con `motivo_error`). Nunca lanza por falta de datos.
- `EstadoJuegoServicio.iniciarJuego(cripta, semilla, ..., forzar=False)` pasa `forzar` a la lógica. La lógica (`_verificarAlIniciar`) verifica con las llaves ya pedidas: resoluble, sin aviso; no resoluble sin forzar, lanza `CriptaNoResoluble` (un `RuntimeError` cuyo mensaje es el reporte); no resoluble con forzar, deja `avisoResolubilidad = aviso_forzado(...)`; error de datos, deja un aviso. Guarda `resultadoVerificacion` en la lógica. No verifica si la reproducción pide `pedir_llaves=False` ni si no hay llaves.
- `ReporteVerificacion.lineas_reporte(resultado)` y `aviso_forzado(resultado)` son funciones puras.
- Hoy el reporte solo se ve en un rechazo, y sale como `Error: <reporte>` desde `main.py` con código 1. `--verificar` y `--forzar` **no** están conectados en `main.py`.
- `ControladorJuego.iniciar()` mezcla entrada, reglas de mapeo y muchos `print` directos; `VistaConsola.mostrar_juego` imprime la sala con 7 secciones y un orden propio (sala, vida, salidas, objetos, enemigos, trampas, inventario, mensajes).

---

## D1. Dónde se arma el reporte al iniciar

**Elegida: el servicio entrega las líneas; el controlador las pasa a la vista; la vista las imprime.** Métodos de lectura nuevos en el servicio: `reporteVerificacion() -> list[str] | None` (líneas de `lineas_reporte(logica.resultadoVerificacion)`, o `None` si no se verificó) y `lineasDeReporte(resultado) -> list[str]` (para `--verificar`, que ya tiene el resultado). El aviso de forzar sigue saliendo de `avisoResolubilidad()` (ya existe).

- Complejidad: O(n) en las líneas del reporte, una sola vez por partida.
- Módulos: `Servicio/EstadoJuegoServicio.py` (dos métodos de solo lectura), `Controlador/ControladorJuego.py`, `Controlador/Vista.py`. Lógica y reporte intactos.

| Alternativa | Complejidad | Módulos afectados | Por qué se descarta |
|---|---|---|---|
| A. La lógica imprime el reporte al terminar `_verificarAlIniciar` | O(n) | `Logica/EstadoJuegoLogica.py` | El modelo no puede conocer la consola (principio IV) y se modificaría la 003, que no debe cambiar. Además la reproducción también pasa por ahí. |
| B. El controlador importa `ReporteVerificacion` de la lógica y arma las líneas | O(n) | `Controlador/ControladorJuego.py` | Rompe la cadena Controlador → Servicio → Lógica: hoy el controlador solo importa DTO y servicio. Duplica la decisión de qué mostrar según el resultado. |
| C. `main.py` verifica y muestra el reporte antes de crear el controlador | O(n) más una verificación extra | `main.py` | La cripta se elige **dentro** del controlador, de forma interactiva: `main.py` aún no la conoce. Obligaría a verificar dos veces (una extra) o a cambiar el flujo del menú. |

**Rechazo.** El controlador atrapa `CriptaNoResoluble` (re-exportada por el servicio para no importar la lógica), muestra el reporte (el mensaje de la excepción) y debajo qué puede hacer el jugador (usar `--forzar` o elegir otra cripta), y `iniciar()` devuelve 1. `main.py` devuelve ese valor en vez del 0 fijo de hoy. El código 1 de un rechazo es el mismo que hoy.

**Cuándo se muestra.** Solo en partida nueva (se llega tras `iniciarJuego`). Una partida cargada no pasa por ahí (supuesto de la spec). Si `reporteVerificacion()` es `None` (sin llaves, FR-313 de la 009), no se muestra reporte y sigue el aviso de llaves que ya existe.

**Orden en pantalla**: primero el reporte; después, si existe, el aviso de forzar (línea `AVISO: …`) para que no se pierda entre el reporte (caso límite de la spec); después el aviso de llaves y los avisos de datos; después el primer turno.

---

## D2. Cómo se construye la pantalla de sala

**Elegida: función pura `texto_sala(...)` que arma una `list` de líneas y devuelve `"\n".join(lineas)`.** `VistaConsola.mostrar_juego` solo hace `print(texto_sala(...))`. Orden fijo (ver [contracts/pantallas.md](contracts/pantallas.md)): sala, salidas, enemigos, objetos, trampas, estado del jugador, mensajes. Una sección vacía muestra su título y «(ninguno)»; nunca desaparece.

- Complejidad: O(n) en tiempo y espacio; `join` es lineal.
- Módulos: `Controlador/Pantallas.py` (nuevo), `Controlador/Vista.py`.

| Alternativa | Complejidad | Módulos afectados | Por qué se descarta |
|---|---|---|---|
| A. Imprimir línea a línea desde la vista (como hoy) | O(n) | `Controlador/Vista.py` | Para probar el texto hay que capturar la salida estándar (como en `test_niebla_vista.py`); el orden y el formato quedan repartidos en decenas de `print`. No se puede comparar sin ejecutar la vista. |
| B. Concatenar con `texto += línea` | O(n²) en el peor caso (CPython la optimiza a veces, no es una garantía) | `Controlador/Pantallas.py` | Se mide en el bloque `pantallas` como **alternativa descartada**; el texto debe ser idéntico al elegido y se informa el tiempo con 100 enemigos. Si no es más lento de forma apreciable, el motivo de descarte pasa a ser que depende de una optimización del intérprete. |
| C. Una plantilla `str.format` con huecos | O(n) | `Controlador/Pantallas.py` | Las secciones tienen cantidad variable de líneas; habría que construir esas partes igual con listas. No simplifica y esconde el orden en una cadena larga. |

**Qué recibe la función (valores simples y DTO ya creados, nada de servicio):** el jugador (`vida_actual`, `vida_max`, `antorcha_encendida`, `antorcha_hasta`), la sala actual con sus objetos, enemigos y trampas, la sala en formato de conocimiento (`SalaConocidaDTO`, de donde salen las salidas, FR-219), el objeto actual, la lista de mensajes y el tiempo actual como entero. Qué llave pide una puerta cerrada lo calcula hoy la vista cruzando salidas reales y conocidas; eso es una **decisión de presentación sobre dos listas**, no una regla del juego, pero para cumplir FR-312 el cruce pasa al controlador (junto con el tiempo actual) y a la función llega ya resuelto como valor.

**Estado de la antorcha**: «encendida hasta t=N» o «apagada», sin calcular nada: `antorcha_hasta` ya viene del modelo.

**Enemigos activos o dormidos**: `EnemigoDTO.activo` ya existe; la función solo lo traduce a la palabra.

---

## D3. Cómo se genera la ayuda

**Elegida: una sola lista de tuplas `COMANDOS = ((nombre, sintaxis, descripción), …)` en `Pantallas.py`.** `texto_ayuda()` la recorre en el orden de la lista. `buscar_comando(primer_termino)` hace una búsqueda lineal (la lista tiene unas 15 filas) y devuelve la fila o `None`. La prueba de claridad verifica que cada comando que el controlador reconoce esté en la lista y que cada fila de la lista sea reconocida.

- Complejidad: ayuda O(k) con k comandos; búsqueda O(k); k es una constante pequeña.
- Módulos: `Controlador/Pantallas.py`; el controlador usa `texto_ayuda()` y reemplaza su prompt largo por una línea corta que menciona `ayuda`.

| Alternativa | Complejidad | Módulos afectados | Por qué se descarta |
|---|---|---|---|
| A. Texto de ayuda fijo escrito a mano | O(1) | `Controlador/Pantallas.py` | Se desactualiza: nada obliga a que coincida con los comandos reales. Hoy el prompt ya los lista a mano y le faltan cosas. |
| B. `dict` de comandos | O(1) por búsqueda | `Controlador/Pantallas.py` | **Prohibido** como índice (constitución I). Con ≈15 filas una búsqueda lineal no se nota. |
| C. Derivar la ayuda de la cadena `if/elif` del controlador | — | `Controlador/ControladorJuego.py` | No se puede leer una cadena de `if` como datos; habría que reescribir el mapeo de comandos, y los comandos existentes deben conservar su sintaxis (FR-313). |

**Lista de comandos (sintaxis actual, sin cambios)**: `norte|sur|este|oeste`, `atacar`, `abrir`, `recoger`, `soltar`, `usar`, `siguiente`/`sig`, `anterior`/`ant`, `esperar`, `inventario [peso|valor|nombre]`, `mapa`, `ir a <id de sala>`, `historia <t>`, `historia #k`, `salir`, y el nuevo `ayuda`. La lista exacta se fija al implementar leyendo el mapeo real del controlador (`cerrar` aparece hoy en el prompt pero el mapeo no lo reconoce, y `guardar` no es un comando: ninguno va en la ayuda; la tarea T004 lo confirma leyendo el controlador).

**El comando nuevo `ayuda` no consume tiempo, no cuenta como acción y no entra al log** (igual que `mapa`).

---

## D4. Dónde se asignan los códigos de salida

**Elegida: `main.py`, con constantes con nombre** (`SALIDA_RESOLUBLE = 0`, `SALIDA_NO_RESOLUBLE = 1`, `SALIDA_ERROR = 2`) y una función `verificar_cripta(servicio, id_cripta) -> int`. Esa función pide `servicio.verificar(...)`, imprime `servicio.lineasDeReporte(resultado)` con `print` (sin vista, principio IV) y devuelve el código según `resultado.resoluble`: `True` → 0, `False` → 1, `None` → 2.

- Complejidad: O(n) en las líneas del reporte; una verificación.
- Módulos: `main.py`.

| Alternativa | Complejidad | Módulos afectados | Por qué se descarta |
|---|---|---|---|
| A. El servicio devuelve el código | O(1) | `Servicio/EstadoJuegoServicio.py` | Un código de salida de proceso es una decisión de la interfaz de línea de comandos, no de un servicio reutilizable (el servicio también lo usa la prueba y el bench). |
| B. El controlador devuelve el código de `--verificar` | O(1) | `Controlador/ControladorJuego.py` | `--verificar` no abre partida ni debe instanciar la vista ni el controlador (constitución IV). |
| C. `ReporteVerificacion` guarda el código | O(1) | `Logica/ReporteVerificacion.py` | Hay que no modificar la verificación ni su reporte (FR-315). |

**Casos del código 2** (clarificación de FR-302): argumento faltante (argparse ya sale con 2: `--verificar` es `nargs=None`, obligatorio al usarse), cripta inexistente o ilegible (`resultado.resoluble is None`), datos no disponibles. Un `OSError`/`RuntimeError` al crear el servicio con `--verificar` también devuelve 2 (hoy el bloque general devuelve 1; con `--verificar` el bloque debe devolver 2).

**Una sola fuente de verdad (hallazgo D1 del análisis)**: `ResultadoVerificacion.codigo_salida()` (003) ya devuelve 0, 1 y 2; `verificar_cripta` devuelve ese valor y las constantes `SALIDA_*` solo dan nombre a esos números, sin repetir la lógica.

**Reporte antes de salir**: se imprime siempre, también cuando `resoluble is None` (las líneas incluyen «NO SE PUDO VERIFICAR» y el motivo).

**Combinaciones**: `--verificar` con `--forzar`: se ignora `--forzar` (la verificación no abre partida). `--verificar` con `--replay` o `--bench`: se rechaza con un mensaje que dice qué pasó y qué hacer, código 2 (mismo patrón que `--hasta` sin `--replay`).

---

## D5. Cómo viaja `forzar`

**Elegida: parámetro explícito por capa**: `leer_argumentos` → `args.forzar` (booleano, `action="store_true"`) → `ControladorJuego(servicio, k_checkpoint=…, forzar=args.forzar)` → `self.servicio.iniciarJuego(id_cripta, semilla, forzar=self.forzar)`.

| Alternativa | Complejidad | Módulos afectados | Por qué se descarta |
|---|---|---|---|
| A. Variable global o de entorno | O(1) | varios | Oculta el flujo, no se puede probar sin alterar el entorno, y rompe FR-305 (alguna capa la decidiría por su cuenta). |
| B. Atributo del servicio que `main.py` fija y el servicio lee | O(1) | `Servicio`, `main.py` | El servicio ya recibe `forzar` como parámetro de `iniciarJuego`; un segundo camino duplica la fuente de verdad. |

Prueba de FR-305: un servicio doble que registra el `forzar` recibido; se comprueba que `main.main(["--forzar"])` y `main.main([])` llegan a `iniciarJuego` con `True` y `False`.

---

## D6. De dónde salen los datos del resumen final

El resumen lleva, en este orden (clarificación de FR-307): motivo, puntaje, acciones, tiempo virtual transcurrido, vida final, salas exploradas.

**Elegida: el controlador junta valores que ya existen y llama a `texto_fin_partida(motivo, puntaje, acciones, tiempo, vida_final, salas_exploradas)`.**

| Dato | De dónde sale hoy |
|---|---|
| motivo | `servicio.terminado()` devuelve `(fin, motivo)`; el motivo ya está en español («El jugador ha muerto», «El jugador ha llegado a la sala final») |
| puntaje | `estadoJuego.puntaje` (la lógica ya lo tiene y `obtenerPuntaje()`); falta un acceso en el servicio: `puntaje()` de solo lectura |
| acciones, tiempo | `servicio.finPartida()` (`acciones_jugador`, `tiempoReloj`) |
| vida final | `servicio.getJudador().vida_actual` |
| salas exploradas | `len(servicio.mapaConocido().salas)` (si la fuente no entrega mapa, 0 y la línea dice «no disponible») |

- Complejidad: O(1) por dato; un único recorrido para el conteo de salas (ya lo hace `mapaConocido()`).
- Módulos: `Controlador/ControladorJuego.py`, `Controlador/Pantallas.py`, `Servicio/EstadoJuegoServicio.py` (un método de lectura).

| Alternativa | Complejidad | Módulos afectados | Por qué se descarta |
|---|---|---|---|
| A. Ampliar `FinPartidaDTO` con puntaje, vida final y salas exploradas | O(1) | `DTO/FinPartidaDTO.py`, `Logica/EstadoJuegoLogica.py` | Toca la lógica y el DTO que usa el registro de puntajes, sin necesidad: todos los datos ya existen. Se reserva si el controlador necesitara más de dos accesos nuevos. |
| B. La función consulta al servicio | O(1) | `Controlador/Pantallas.py` | Deja de ser pura: las pruebas necesitarían un servicio; viola el objetivo de «funciones que reciben los datos ya listos». |

**Motivo «u otro»**: si el motivo llega vacío o `None`, la función muestra «Motivo no informado» (nunca vacío, caso límite de la spec).

**Orden de lo que se imprime al terminar** (se conserva el actual para no cambiar el flujo): banner de fin, registro de puntaje, ruta del log, últimos mensajes, resumen final. Lo que cambia es el texto del banner y del resumen. El resumen anterior (`ID Cripta`, `Versión`, `Enemigos derrotados`) conserva esos datos en una línea de contexto debajo del bloque fijo, porque la tabla de puntajes ya los usa; la lista exacta está en el contrato.

---

## D7. Mensajes de error y rechazo

**Elegida: función `texto_error(que_paso, que_hacer) -> str`** que devuelve `"<qué pasó> <qué puede hacer>"` en el mismo formato siempre, y un **catálogo de mensajes** (funciones o constantes con nombre en `Pantallas.py`) para los rechazos que el controlador hoy escribe en línea (salida inexistente, puerta cerrada, comando no reconocido, `ir a` con destino inválido, `historia` mal escrita, inventario vacío…).

- Complejidad: O(1) por mensaje.
- Módulos: `Controlador/Pantallas.py`, y en `Controlador/ControladorJuego.py` los `print("…")` de rechazo pasan a `print(texto_error(…))` o al mensaje del catálogo.

| Alternativa | Complejidad | Módulos afectados | Por qué se descarta |
|---|---|---|---|
| A. Dejar los textos sueltos y solo corregir los que falten | O(1) | `Controlador/ControladorJuego.py` | No hay forma de comprobar que **todos** dicen qué pasó y qué hacer; el criterio SC-306 exige una prueba que lo verifique sobre el catálogo completo. |
| B. Excepciones propias con mensaje | O(1) | `Logica`, `Servicio` | Los mensajes de la lógica ya existen y no deben cambiar en esta capacidad; las excepciones del modelo que hoy se muestran con `Error: {e}` se envuelven en la presentación: `texto_error("No se pudo …: {e}", "…")`. |

**Los mensajes del modelo** (por ejemplo `str(error)` de `ValueError` en `ir a`) no se reescriben: se anteponen con el contexto («No se puede viajar: …») y se añade qué hacer.

**Prueba de claridad** (SC-306, SC-307): para cada entrada del catálogo se comprueba que (a) tiene las dos partes, (b) no contiene secuencias de escape ANSI, (c) no contiene palabras de una lista corta de términos en inglés comunes que se coló en mensajes (`error`, `invalid`, `not found` — «Error» como palabra del español se acepta solo como inicio de frase de la forma actual `Error: …`; ver nota), y (d) la ayuda lista todo comando que el controlador reconoce.

*Nota de alcance*: «Error:» es también castellano; la lista de términos en otro idioma se limita a palabras claramente inglesas (`invalid`, `not found`, `failed`, `unknown`).

---

## D8. Estado de la puerta en la pantalla de sala

La spec (FR-306) pide «abierta o cerrada». Con la niebla de guerra (002, FR-219) una puerta que el jugador aún no observó no se muestra ni como abierta ni como cerrada. La vista actual ya tiene una tercera etiqueta: «Sin observar».

**Elegida: tres etiquetas (`abierta`, `cerrada`, `sin observar`) con el mismo formato.** Es un caso que FR-306 no menciona pero que 002 exige para no revelar lo no visto; se registra como supuesto de esta capacidad (sección Supuestos de la spec) y no cambia ningún requisito: abierta y cerrada se muestran siempre que se conocen.

| Alternativa | Por qué se descarta |
|---|---|
| A. Solo abierta/cerrada | Para una puerta no observada habría que adivinar o mostrar el estado real, que revela información que 002 manda ocultar. |

Cuenta como corrección de la especificación (principio X): se añade el supuesto a `spec.md` en una confirmación propia **antes** del código.

---

## Mediciones previstas

Contrato en [contracts/bench-pantallas.md](contracts/bench-pantallas.md). Lo que se mide y con qué criterio:

| Qué | Elegida | Descartada | Criterio |
|---|---|---|---|
| Sala con 0, 10 y 100 enemigos | lista + `join` | `+=` | Texto idéntico (duro); sala con 100 enemigos < 20 ms (duro); razón de tiempos (informa) |
| Resumen final | lista + `join` | `+=` | Texto idéntico (duro) |
| Ayuda | recorrido de la tabla | texto fijo | Informa |
| Ciclo de eventos | `--bench ciclo` sin cambios | — | < 20 ms (duro, ya existente) |

Las pantallas no están dentro del ciclo de eventos (se construyen entre decisiones del jugador); aun así se vuelve a ejecutar `ciclo` para dejar constancia en `DECISIONES.md` de que el camino de eventos no cambió.

---

## Línea base (T001, T002; 2026-11-13, antes de cualquier cambio)

Se usa el intérprete del entorno virtual del repositorio (`.venv/Scripts/python.exe`): con el Python del sistema falta `requests` y `test_sin_red.py` y otros 15 módulos no se importan (16 errores de importación ajenos a esta capacidad).

**Suite completa** (`.venv/Scripts/python.exe -m unittest discover -p "test_*.py"`): **635 pruebas, todas OK**, 41 s. No hay pruebas fallando hoy. Pruebas que dependen del texto de la vista o del controlador (fase 2): `test_niebla_vista.py`, `test_terreno_costos.py`, `test_viaje_comando.py`, `test_resolubilidad_reporte.py`, `test_historia_tiempo.py`, `test_historia_accion.py`, `test_cazador.py`, `test_equivalencia_cazador.py`, `test_cli_checkpoint.py`, `test_replay_hasta.py`, `test_determinismo_replay.py`, `tests_labs/prueba_reporte_solicitudes.py`, `tests_labs/escenarios_terreno.py`, `bench/llaves.py`.

**`--bench ciclo`** (antes):

| Carga | Mediana | Máximo | Veredicto |
|---|---|---|---|
| 10 esbirros activos | 281,7 µs | 712,3 µs | CUMPLE |
| 100 esbirros activos | 2,67 ms | 7,50 ms | CUMPLE |
| 300 esbirros activos | 8,41 ms | 16,14 ms | CUMPLE |
| 1 000 esbirros (estrés, informativo) | 30,96 ms | 101,26 ms | no decide |
| 10 cazadores persiguiendo | 444,7 µs | 779,7 µs | CUMPLE |
| 50 cazadores persiguiendo | 2,23 ms | 3,27 ms | CUMPLE |
| Reproducir 300 acciones | 203,34 ms | 208,12 ms | informativo |

## Pruebas en rojo esperadas (T016, fase 2 cerrada)

Suite completa tras actualizar las pruebas existentes: 636 pruebas, **5 fallan, y son exactamente las anunciadas**:

| Prueba | Texto que cambia | Se pone en verde en |
|---|---|---|
| `test_terreno_costos.TestVista.test_FR131_el_cazador_se_distingue_de_los_demas_enemigos` | filas de la sección `--- ENEMIGOS ---`: `[cazador]` en minúsculas y `[activo]`/`[dormido]` | T032 y T035 |
| `test_viaje_comando.TestComandoRechazado.test_FR237_un_destino_que_no_es_un_numero_no_llama_al_servicio` (4 subcasos) | `El destino debe ser el número de una sala.` → `El destino de 'ir a' debe ser el número de una sala. Ejemplo: ir a 12.` | T034 y T036 |

**Pruebas que ya pasaban y se amplían** (`test_niebla_vista.py`): la puerta «sin observar» en la **sala** (FR-306), y el `ServicioFalso` del comando `mapa` gana `tiempoActual`, `puntaje`, `reporteVerificacion`, `avisoResolubilidad` y `avisoLlaves` (el controlador nuevo los usa).

**Revisadas, sin cambio de texto** (T009, T010, T011, T012, T013, T015): `test_resolubilidad_reporte.py` (los textos de `lineas_reporte` y `aviso_forzado` no cambian y ningún aserto depende de `Error:`), `test_historia_tiempo.py` (la secuencia de entradas sigue válida: el reporte no pide entrada), `test_historia_accion.py` (la revisión de `Controlador/*.py` recoge `Pantallas.py` sola; la comprobación de importaciones de `Pantallas.py` se hace solo en `test_pantallas_aislamiento.py`, T019, para no duplicarla), `test_cazador.py`, `test_equivalencia_cazador.py`, `tests_labs/escenarios_terreno.py`, `bench/llaves.py` (solo usan `ControladorJuego(None)._mapear_entrada_a_evento`), `test_cli_checkpoint.py` y `test_replay_hasta.py` (ningún aserto contiene los textos con caracteres dañados).

**Hallazgo ajeno (T014)**: `tests_labs/prueba_reporte_solicitudes.py` es un script de laboratorio, no una prueba de la suite (`test_*.py`), y **ya falla hoy** por una causa anterior: sus teclas simuladas no incluyen la pregunta de la tabla de puntajes (`IndexError: pop from empty list`), así que nunca llega a su aserto de `Reproducción terminada`. No se arregla en esta capacidad; la corrección de los caracteres dañados (T037) sí deja correcto el texto que ese aserto espera.
