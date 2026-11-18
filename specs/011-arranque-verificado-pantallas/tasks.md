# Tareas: Arranque verificado y pantallas de consola claras

**Entrada**: `specs/011-arranque-verificado-pantallas/` (spec.md, plan.md, research.md, data-model.md, contracts/, quickstart.md)

**Requisitos previos**: plan.md, spec.md y las 3 clarificaciones de la sesión 2026-11-13.

**Pruebas**: SÍ se piden (plan.md, «Pruebas»; FR-317, SC-301 a SC-308, donde SC-308 se verifica solo a mano en T042 y T047; constitución IX). Se escriben **antes** del código de cada historia y deben fallar primero.

**Organización**: por historia (US1 arranque verificado, US2 pantallas claras; ambas P1 y se implementan juntas). La fase 2 actualiza las pruebas existentes que dependen del texto de la vista y va **antes** de tocar la vista.

## Formato: `[ID] [P?] [Historia] Descripción con ruta`

- **[P]**: se puede hacer en paralelo (archivos distintos, sin depender de una tarea sin terminar).
- **[US1] / [US2]**: historia de la spec. Setup, Fundamentos, Bench y Pulido no llevan etiqueta.
- Cada tarea cita los requisitos que atiende (FR-3xx, constitución VIII).
- Orden de confirmaciones (constitución X): primero la corrección de `spec.md` (T003), luego las pruebas actualizadas (fase 2), luego el código.

## Convenciones de ruta

Repositorio en la raíz: `main.py`, `Controlador/`, `Servicio/`, `bench/`, `tests_labs/`, pruebas `test_*.py` en la raíz, documentos en la raíz y en `specs/011-arranque-verificado-pantallas/`.

---

## Fase 1: Preparación

**Propósito**: línea base antes de cambiar nada y corrección de la especificación.

- [X] T001 Ejecutar la suite completa (`python -m unittest discover -p "test_*.py"`) y guardar en `specs/011-arranque-verificado-pantallas/research.md` (sección «Línea base») cuántas pruebas pasan, cuáles fallan ya hoy y cuáles dependen de texto de la vista; sirve para distinguir fallos nuevos de los anteriores. (FR-317)
- [X] T002 [P] Registrar la línea base de medición: ejecutar `python main.py --bench ciclo` y copiar las cifras (mediana y máximo con 10, 100, 300 y 1 000 enemigos y con cazadores) a `specs/011-arranque-verificado-pantallas/research.md`, sección «Línea base», para el antes y el después. (constitución VII)
- [X] T003 Corregir `specs/011-arranque-verificado-pantallas/spec.md` (principio X): añadir en «Supuestos» que una puerta cuyo estado el jugador aún no observó se muestra como «sin observar» (niebla de guerra, 002 FR-219), de modo que las etiquetas de estado de FR-306 son abierta, cerrada y sin observar; añadir a FR-306 la referencia a ese supuesto. Hacerlo en una confirmación propia, **antes** de cualquier código. (FR-306) **Hecho antes de generar estas tareas** (confirmación propia de la spec): FR-306, el escenario 1 de la historia 2 y «Supuestos» ya incluyen «sin observar», y FR-308 ya incluye los caracteres dañados; solo queda comprobar que `spec.md` y `research.md` D8 dicen lo mismo.
- [X] T004 [P] Leer `Controlador/ControladorJuego.py` (`_mapear_entrada_a_evento`, `iniciar`, `_procesar_comando_*`) y fijar la lista real de comandos y sus sinónimos (`siguiente`/`sig`, `anterior`/`ant`, `inventario [peso|valor|nombre]`, `ir a <n>`, `historia <t>`, `historia #k`, `salir`, y comprobar si `cerrar` se reconoce: hoy el prompt lo anuncia pero no se vio en el mapeo). Anotar el resultado en `specs/011-arranque-verificado-pantallas/contracts/pantallas.md` §3; **no inventar** comandos: si `cerrar` no existe, quitarlo de la ayuda y dejarlo anotado. (FR-309, FR-313)
- [X] T005 [P] Listar en `specs/011-arranque-verificado-pantallas/contracts/pantallas.md` §5 todos los `print` de rechazo o error del controlador (salida inexistente, puerta cerrada, abrir/recoger/atacar sin objetivo, números inválidos, inventario vacío, historia, ir a, carga y guardado de partida, sin criptas) con su texto actual y el texto nuevo «qué pasó + qué hacer». Es el catálogo que implementa T034. (FR-308, FR-310)

---

## Fase 2: Pruebas existentes que dependen del texto de la vista

**Propósito**: actualizar de forma explícita, **antes de tocar la vista**, cada prueba que compara texto de la vista o del controlador (FR-317). Todas las tareas de esta fase pueden hacerse en paralelo (archivos distintos). Las que cambian de texto quedan **en rojo** hasta las fases 4 y 5; las que no cambian se comprueban y se dejan anotadas. Una sola confirmación con la lista antes/después en el mensaje.

- [X] T006 [P] `test_niebla_vista.py` — `TestVista`/`mostrar_juego` (líneas ~37, ~125): la pantalla de sala cambia de formato. Textos que se mantienen: `sala sin explorar`, `costo 250`, `cerrada`, `este`; `Pasillo (id 2)` y `sin observar` del **mapa** no cambian (el mapa no se toca). Cambian: el título `--- SALIDAS ---` y la forma de cada salida (`este  -> destino  [estado]  costo N`, contrato §1); añadir la comprobación de la etiqueta `sin observar` de una puerta no observada en la **sala** (FR-306) y que ninguna sala avistada muestre su id ni su nombre (FR-219). Además `ServicioFalso` del test `mapa` (líneas ~155-170) debe ganar los métodos nuevos que ahora usa el controlador (`tiempoActual`, `puntaje`, `reporteVerificacion`, `avisoResolubilidad`, `avisoLlaves`) con valores fijos; el aserto `MAPA CONOCIDO` no cambia. (FR-306, FR-312, FR-317)
- [X] T007 [P] `test_terreno_costos.py` — `TestVista` (líneas ~157-185): `test_FR130_*` sigue válido (`costo 70`, `costo 250`, `costo 100`, `sala sin explorar`, no aparece `Sala 3`). `test_FR131_el_cazador_se_distingue…` cambia: hoy filtra líneas con `Vida:` sin `JUGADOR` y la marca `[CAZADOR]`; en el formato nuevo la línea de enemigo es `- [cazador] <nombre> [activo|dormido]  vida a/b` y la vida del jugador está en `Vida:` bajo `ESTADO DEL JUGADOR`. Reescribir el filtro con la sección `--- ENEMIGOS ---` y la marca `[cazador]` en minúsculas; añadir que un enemigo dormido muestra `[dormido]`. (FR-306, FR-317)
- [X] T008 [P] `test_viaje_comando.py` (líneas ~60-75): `Llegaste a la sala 4 tras 2 pasos (tiempo 200).` y `Esa sala no está explorada.` se mantienen como subcadena (el rechazo gana un «qué hacer» después, p. ej. `Usa 'mapa'…`). Cambia `El destino debe ser el número de una sala.` por el texto nuevo del contrato §5: `El destino de 'ir a' debe ser el número de una sala. Ejemplo: ir a 12.`; mantener `reconocido == True`, que el servicio no se llame y que el reloj no cambie. (FR-310, FR-313, FR-317)
- [X] T009 [P] `test_resolubilidad_reporte.py` — revisar `CodigosDeSalida` y `VerificarSinPartida`: los textos de `lineas_reporte` y de `aviso_forzado` **no cambian** (FR-315), así que sus asertos quedan igual. Comprobar y anotar en el mensaje de la confirmación que ningún aserto depende de `Error:` ni del orden de impresión de `main.py`. La comprobación de que `ResultadoVerificacion.codigo_salida()` (0, 1, 2) coincide con las constantes de `main.py` se escribe en T020, porque depende de T024. (FR-302, FR-315, FR-317)
- [X] T010 [P] `test_historia_tiempo.py` — `TestControladorHistoria` (líneas ~200-265): usa el servicio real, `input` simulado y `sys.stdout` anulado; los comandos `historia` y `esperar` no cambian de sintaxis. Comprobar que la secuencia de entradas `n, n, 1, n, esperar, …, salir, n` sigue siendo válida: con el flujo nuevo aparece el reporte al iniciar sin pedir ninguna entrada nueva. Sin cambio de texto esperado; anotarlo en el mensaje de la confirmación de la fase 2 (lista «sin cambio»). Si el flujo agrega una pregunta, actualizar la lista de entradas. (FR-301, FR-313, FR-317)
- [X] T011 [P] `test_historia_accion.py` — `TestControladorNoPenetraCapaServicio` (líneas ~345-380): revisa **todos** los `.py` de `Controlador/` buscando `servicio._algo`; el archivo nuevo `Controlador/Pantallas.py` entra solo en la revisión. Sin cambio de texto; añadir (en esta misma clase) que `Pantallas.py` no contiene `import Servicio` ni `import Logica`. (FR-312, constitución IV)
- [X] T012 [P] `test_cazador.py`, `test_equivalencia_cazador.py` y `tests_labs/escenarios_terreno.py` — usan `ControladorJuego(None)._mapear_entrada_a_evento(...)`, no texto. Sin cambio: la firma `ControladorJuego(servicio, k_checkpoint=None, forzar=False)` debe seguir aceptando `ControladorJuego(None)` y `_mapear_entrada_a_evento(accion, sala, jugador)` conserva sus parámetros y sus retornos (`EventoDTO`, `"IGNORAR"`, `None`). Anotarlo en el mensaje de la confirmación de la fase 2 (lista «sin cambio»); no editar esos archivos salvo que falle. (FR-313, FR-317)
- [X] T013 [P] `test_cli_checkpoint.py` y `test_replay_hasta.py` (líneas ~30-65 y ~255-285): comparan mensajes de `argparse` y de `main` (`mayor o igual que 1`, `no es un número entero`, `el instante virtual debe ser mayor o igual que 0`, `Error: el argumento --hasta requiere especificar una partida con --replay.`). Estos textos **no cambian** (ya dicen qué pasó y qué hacer). Cuidado: T037 corrige los caracteres dañados de `main.py`; verificar que ninguno de estos asertos incluye uno de los textos con `Ã`. Los casos nuevos de `--verificar` y `--forzar` en `test_cli_checkpoint.py` se escriben en T020, porque dependen de T024. (FR-317)
- [X] T014 [P] `tests_labs/prueba_reporte_solicitudes.py` (línea ~93) y `test_determinismo_replay.py`: la primera exige el texto correcto `Reproducción terminada` antes del reporte de solicitudes, pero `main.py` hoy imprime `ReproducciÃ³n terminada`, así que **hoy ese aserto no puede cumplirse**. Confirmar con la línea base (T001) y dejar escrito que pasa a verde con T029 (FR-308). `test_determinismo_replay.py` compara el estado, no texto; sin cambio. (FR-308, FR-317)
- [X] T015 [P] `bench/llaves.py` (líneas ~34, ~260): usa `ControladorJuego(None)` solo para `_mapear_entrada_a_evento`; sin cambio de texto. Anotar en el mensaje de la confirmación de la fase 2 (lista «sin cambio»). Verificar además que `python main.py --bench llaves` sigue dando CUMPLE al final de la fase 5. (FR-313, FR-317)
- [X] T016 Ejecutar la suite completa y comparar con T001: la lista de pruebas en rojo debe ser **exactamente** la que anuncian T006, T007 y T008 (más la de T014 si ya fallaba); cualquier otra es un error de esta fase. Dejar la lista en `specs/011-arranque-verificado-pantallas/research.md`, sección «Pruebas en rojo esperadas». (FR-317)

**Punto de control**: pruebas existentes actualizadas y explicadas; solo fallan las anunciadas. Ahora sí se puede tocar la vista.

---

## Fase 3: Fundamentos (bloquea las dos historias)

**Propósito**: piezas comunes de lectura y de texto que usan US1 y US2. No agregan comportamiento visible.

- [X] T017 Añadir en `Servicio/EstadoJuegoServicio.py` métodos **de solo lectura** (sin tocar la lógica): `reporteVerificacion() -> list[str] | None` (líneas de `lineas_reporte(logica.resultadoVerificacion)`, o `None` si no se verificó o no hay partida iniciada), `lineasDeReporte(resultado) -> list[str]` (para `--verificar`), `tiempoActual() -> int` (`estadoJuego.reloj.tiempo_actual`) y `puntaje() -> int` (envuelve `obtenerPuntaje`); re-exportar `CriptaNoResoluble` (`from Logica.VerificacionResolubilidad import CriptaNoResoluble`) para que el controlador no importe la lógica. No cambia ningún método existente. (FR-301, FR-307, FR-312, FR-315; research D1, D6)
- [X] T018 [P] Crear `Controlador/Pantallas.py` con la lista `COMANDOS` (tuplas `(nombre, sintaxis, descripcion)` según T004), `buscar_comando(termino)` (búsqueda lineal, devuelve la fila o `None`; **sin dict ni set**) y `texto_error(que_paso, que_hacer)` que devuelve `"<que_paso> <que_hacer>"` y lanza `ValueError` si alguna parte está vacía. Módulo sin `print`, sin importar `Servicio` ni `Logica`, sin colores. «No hay dos filas con el mismo `nombre`». (FR-309, FR-310, FR-311, FR-316; research D3, D7)
- [X] T019 [P] Escribir `test_pantallas_aislamiento.py`: (a) `Controlador/Pantallas.py` no importa `Servicio`, `Logica` ni `adaptadores`; (b) ni los archivos nuevos ni los tocados usan `dict`/`set` como índice, `sorted(`, `.sort(`, `heapq`, `bisect`, `collections`, `networkx` (búsqueda de texto sobre `Controlador/Pantallas.py`, `bench/pantallas.py` y las líneas nuevas de `main.py`); (c) la vista imprime **exactamente** lo que devuelve la función de pantalla (con una función sustituida por un texto fijo). Debe fallar hasta T032. (FR-312, FR-316, constitución I y IV)

**Punto de control**: el servicio expone lo que hace falta; `Pantallas.py` existe con tabla y errores.

---

## Fase 4: Historia 1 — Arranque verificado (P1)

**Objetivo**: reporte de resolubilidad al iniciar, `--verificar`, `--forzar` y códigos de salida.

**Convención de nombres (constitución IX)**: cada prueba se llama `test_FR3xx_<descripción>` con el id del requisito que cubre (por ejemplo `test_FR305_forzar_viaja_hasta_la_logica`), como en las demás capacidades, para que la trazabilidad se pueda buscar con el id.

**Prueba independiente**: con una cripta resoluble y otra no resoluble, con y sin `--forzar`, y `--verificar` sobre ambas y sobre una inexistente: texto, apertura de partida y código de salida.

### Pruebas de la historia 1 (primero; deben fallar)

- [X] T020 [P] [US1] Escribir `test_arranque_verificado.py` — **códigos de salida de `--verificar`** (FR-302, SC-302): con el patrón de `tests_labs/prueba_reporte_solicitudes.ejecutar` (sustituir `crear_servicio` y `input`) y los casos del Apéndice B de `test_resolubilidad_reporte.py`: cripta resoluble (`B-R3`) → `main.main(["--verificar", id]) == 0` y el reporte `RESOLUBLE` impreso; no resoluble (`B-R1`) → 1 y `NO RESOLUBLE`; inexistente → 2 y `NO SE PUDO VERIFICAR` con el motivo; sin valor → 2. En los tres casos: no se abre partida ni log (`AlmacenLogTexto.abrir` no se llama), **no se crea la vista** (`VistaConsola.__init__` falla si se llama) y el reporte salió antes del retorno. Incluir que `--verificar --forzar` ignora `--forzar`, y que `--verificar` con `--replay` o `--bench` devuelve 2 con un mensaje que dice qué hacer. Comprobar que cada código coincide con `ResultadoVerificacion.codigo_salida()` y con las constantes `SALIDA_*` de `main.py` (comprobación movida desde T009). Añadir también en `test_cli_checkpoint.py` los casos de `leer_argumentos(["--verificar", "x"])` y `leer_argumentos(["--forzar"])` (valores `"x"` y `True`) y que `--verificar` sin valor termina con código 2 (movido desde T013).
- [X] T021 [P] [US1] En `test_arranque_verificado.py` — **reporte al iniciar** (FR-301, SC-301): partida nueva con cripta resoluble: el reporte `RESOLUBLE` sale **antes** de la primera pantalla de sala y la partida se abre; cripta no resoluble sin `--forzar`: sale el reporte, sale la guía de qué hacer (contrato `pantallas.md` §5, «Cripta no resoluble»), la partida **no** se abre (sin log) y `main.main` devuelve 1; cripta no resoluble con `--forzar`: reporte, luego la línea `AVISO: …` de `aviso_forzado` **antes** del primer turno, y la partida se abre; cripta resoluble con `--forzar`: sin aviso de forzar; verificación no disponible: reporte `NO SE PUDO VERIFICAR` y aviso de la 003, partida abierta; partida cargada: **sin** reporte; **sin criptas disponibles**: mensaje con qué hacer y `main.main` devuelve 1.
- [X] T022 [P] [US1] En `test_arranque_verificado.py` — **viaje de `forzar`** (FR-305): servicio doble que registra el `forzar` recibido en `iniciarJuego`; `main.main(["--forzar"])` lo recibe `True` y `main.main([])` lo recibe `False`; y una prueba de que `ControladorJuego(servicio, forzar=True)` lo pasa tal cual y que ninguna capa lo fija por su cuenta (se revisa que `ControladorJuego.__init__` lo toma del parámetro y que el valor por defecto es `False`).
- [X] T023 [P] [US1] En `test_arranque_verificado.py` — **sin efectos en el log ni en el guardado** (FR-304, FR-315): iniciar con y sin `--forzar` la misma cripta no resoluble y comparar: `partida.log` idéntico línea por línea (no aparece `forzar`), y el archivo de guardado se genera igual (mismo formato 8 / estado 5). La advertencia sale una sola vez, al iniciar.

### Implementación de la historia 1

- [X] T024 [US1] En `main.py`: añadir `--verificar CRIPTA` y `--forzar` (`action="store_true"`) a `leer_argumentos` con los textos de ayuda del contrato `cli-argumentos.md` §1; definir `SALIDA_RESOLUBLE = 0`, `SALIDA_NO_RESOLUBLE = 1`, `SALIDA_ERROR = 2`; añadir `verificar_cripta(servicio, id_cripta) -> int` que llama a `servicio.verificar(...)`, imprime `servicio.lineasDeReporte(resultado)` con `print` **sin crear la vista ni el controlador** y devuelve `resultado.codigo_salida()` (el DTO de la 003 ya da 0, 1 y 2: no se repite la lógica; las constantes `SALIDA_*` solo dan nombre a esos valores). Rechazar `--verificar` con `--replay` o `--bench` con un mensaje en español (qué pasó y qué hacer) y código 2; ignorar `--forzar` junto a `--verificar`. Dentro del bloque de errores generales, si el modo es `--verificar` devolver 2 en vez de 1. (FR-302, FR-303, FR-310, FR-316; research D4)
- [X] T025 [US1] En `main.py`: construir `ControladorJuego(servicio, k_checkpoint=args.checkpoint_cada, forzar=args.forzar)` y devolver el valor que entrega `iniciar()` (0 normal, 1 rechazo por cripta no resoluble) en lugar del 0 fijo; mantener 130 para Ctrl+C y el 1 de los errores generales. (FR-303, FR-305; research D5)
- [X] T026 [US1] En `Controlador/ControladorJuego.py`: `__init__(self, servicio, k_checkpoint=None, forzar=False)` guarda `self.forzar`; en el arranque, `self.servicio.iniciarJuego(id_cripta, semilla, forzar=self.forzar)`. Atrapar `CriptaNoResoluble` (importada de `Servicio.EstadoJuegoServicio`): mostrar el reporte (el mensaje de la excepción), la guía de qué hacer (`texto_error`, contrato `pantallas.md` §5) y devolver 1 desde `iniciar()` sin abrir la partida; si no hay criptas disponibles, imprime el mensaje del catálogo («Sin criptas», `pantallas.md` §5) y devuelve 1; el resto de `iniciar()` devuelve 0. (FR-301, FR-303, FR-305, FR-310)
- [X] T027 [US1] En `Controlador/Vista.py`: añadir `mostrar_reporte_verificacion(lineas)` (imprime las líneas recibidas, sin decidir nada) y `mostrar_aviso(texto)`; en `ControladorJuego.iniciar()`, tras `iniciarJuego`, mostrar en este orden: reporte de `servicio.reporteVerificacion()` (si no es `None`), aviso de `servicio.avisoResolubilidad()` (si existe), aviso de llaves, advertencias de datos y recién entonces el primer turno. No se muestra nada de esto al cargar una partida. (FR-301, FR-304, FR-311, FR-312; research D1)

**Punto de control**: T020 a T023 en verde; `python main.py --verificar <cripta>` y el arranque cumplen el contrato `cli-argumentos.md`.

---

## Fase 5: Historia 2 — Pantallas de consola claras (P1)

**Objetivo**: pantalla de sala estable, resumen final, ayuda y mensajes claros, todo en español y verificable con pruebas de texto.

**Convención de nombres (constitución IX)**: cada prueba se llama `test_FR3xx_<descripción>` con el id del requisito que cubre, como en la fase 4.

**Prueba independiente**: con datos fijos, comparar el texto exacto de la sala, del resumen, de la ayuda y de los mensajes de rechazo, dos veces seguidas.

### Pruebas de la historia 2 (primero; deben fallar)

- [X] T028 [P] [US2] Escribir `test_pantallas_texto.py` — **pantalla de sala** (FR-306, FR-311, SC-304, SC-305): ≥ 5 situaciones con texto exacto esperado (contrato `pantallas.md` §1): sala vacía (todas las secciones con `(ninguna)` / `(ninguno)`, mismo orden), sala con enemigos activos y dormidos y un cazador (`[cazador]`), sala con puertas `abierta`, `cerrada`, `cerrada, requiere <llave>` y `sin observar` (**la etiqueta «sin observar»** y que una sala avistada no revele su nombre ni su id), sala con objetos y trampas, y sin mensajes frente a con 20 mensajes. Cada situación se construye **dos veces** y los textos deben ser iguales carácter por carácter; el estado del jugador muestra siempre `Vida`, `Tiempo` y `Antorcha` (`encendida hasta t=N` o `apagada`) en ese orden; sin `\x1b` ni tabulaciones.
- [X] T029 [P] [US2] En `test_pantallas_texto.py` — **resumen de fin de partida** (FR-307): texto exacto con los seis rótulos fijos en el orden `Motivo`, `Puntaje`, `Acciones`, `Tiempo`, `Vida final`, `Salas exploradas` y la línea final de cripta, versión y enemigos derrotados; motivo `None` o vacío → `Motivo no informado`; sin mapa → `no disponible`; los dos motivos reales (`El jugador ha muerto`, `El jugador ha llegado a la sala final`).
- [X] T030 [P] [US2] En `test_pantallas_texto.py` — **ayuda y claridad** (FR-308 a FR-310, SC-306, SC-307): (a) `texto_ayuda()` contiene una fila por cada entrada de `COMANDOS`, con su sintaxis, incluidas `mover` (`norte|sur|este|oeste`), `mapa`, `ir a <id de sala>`, `historia <t>`, `historia #k`, `ayuda` y `salir`; (b) **cada comando que reconoce el controlador** (los de T004) está en la tabla y cada fila de la tabla es reconocida (sin sinónimos huérfanos); (c) cada mensaje del catálogo de T005 tiene las dos partes (qué pasó y qué hacer), está en español, no contiene `\x1b` ni palabras `invalid`, `not found`, `failed`, `unknown`; (d) `texto_error` con una parte vacía lanza `ValueError`; (e) la ayuda posterior a la partida solo lista `historia <t>`, `historia #k`, `ayuda` y `salir`.
- [X] T031 [P] [US2] Escribir `test_pantallas_controlador.py` con un servicio falso (como el de `test_niebla_vista.py`): (a) escribir `ayuda` en la partida imprime la ayuda **sin** consumir tiempo, sin contar como acción y sin entrar al log; (b) al terminar la partida (muerte y llegada) se imprime el resumen con los seis datos que entrega el servicio falso y el prompt de entrada es el corto (`¿Qué deseas hacer? (escribe 'ayuda' para ver los comandos): `); (c) un comando desconocido imprime el mensaje del catálogo con «qué pasó» y «qué hacer»; (d) **los comandos existentes conservan su sintaxis** (`norte`, `mapa`, `ir a 3`, `historia 5`, `historia #2`, `inventario peso`, `siguiente`/`sig`, `salir`) y siguen reconocidos con el mismo resultado de antes; (e) **ningún rechazo queda fuera del catálogo**: una prueba lee `Controlador/ControladorJuego.py` y comprueba que sus `print` de error o rechazo pasan por `texto_error` (sin literales de rechazo sueltos), y otra fuerza cada rechazo del catálogo y comprueba que trae las dos partes. (FR-307, FR-309, FR-310, FR-313)

### Implementación de la historia 2

- [X] T032 [US2] En `Controlador/Pantallas.py`: implementar `texto_sala(jugador, tiempo, sala, sala_conocida, llaves, objeto_actual, mensajes)` según el contrato `pantallas.md` §1 (lista de líneas + `"\n".join`; secciones y orden fijos; vacíos con `(ninguno)`/`(ninguna)`; estados `abierta`, `cerrada`, `cerrada, requiere <llave>`, **`sin observar`**; destino solo si está explorado; `[cazador]`; enemigo `[activo]`/`[dormido]` leyendo `EnemigoDTO.activo`; antorcha desde `antorcha_encendida`/`antorcha_hasta`), sin leer el servicio ni calcular nada del juego, y mantener la **vía descartada** `texto_sala_concatenado` solo dentro de `bench/pantallas.py` (T038), no aquí. (FR-306, FR-311, FR-312, FR-316; research D2, D8)
- [X] T033 [US2] En `Controlador/Pantallas.py`: implementar `texto_fin_partida(motivo, puntaje, acciones, tiempo, vida_final, salas_exploradas, id_cripta, version, enemigos_derrotados)` (contrato §2) y `texto_ayuda(post_partida=False)` (contrato §3) a partir de `COMANDOS`. (FR-307, FR-309, FR-311; research D3, D6)
- [X] T034 [US2] En `Controlador/Pantallas.py`: añadir el catálogo de mensajes de T005 como funciones o constantes con nombre que usan `texto_error` (salida inexistente, puerta cerrada con y sin llave, comando no reconocido, `ir a` inválido, `historia` mal escrita, inventario vacío, número de cripta inválido, sin criptas, partida no cargada, cripta no resoluble). Los mensajes que vienen del modelo se envuelven como `<contexto>: <mensaje del modelo>. <qué hacer>` sin reescribir el texto del modelo. (FR-308, FR-310; research D7)
- [X] T035 [US2] En `Controlador/Vista.py`: `VistaConsola.mostrar_juego(jugador, sala_actual, sala_conocida, objeto_actual=None, mensajes=None, tiempo=None, llaves=None)` pasa a `print(texto_sala(...))` (los cinco primeros parámetros conservan su orden para no romper las llamadas existentes); añadir `mostrar_fin_partida(...)`, `mostrar_ayuda(...)` y `mostrar_error(texto)` que solo imprimen lo recibido. `mostrar_mapa_conocido`, `mostrar_viaje` (el rechazo gana el «qué hacer»), `mostrar_inventario`, `mostrar_puntajes` e `mostrar_historia` conservan su formato. Quitar de la vista el cruce de salidas reales y conocidas para la llave (pasa al controlador, T036). (FR-306, FR-311, FR-312; research D2)
- [X] T036 [US2] En `Controlador/ControladorJuego.py`: (a) construir en cada turno las `llaves` pedidas por las salidas cerradas cruzando `sala.salidas` con `sala_conocida.salidas`, pedir `servicio.tiempoActual()` y llamar a `mostrar_juego(..., tiempo, llaves)`; (b) reemplazar el prompt largo por el corto de T031; (c) interpretar `ayuda` (no consume tiempo, no es acción, no entra al log) y `ayuda` también en la fase posterior a la partida; (d) en el fin de partida reunir `servicio.terminado()` (motivo), `servicio.puntaje()`, `finPartida()` (acciones, tiempo, cripta, versión, enemigos derrotados), `getJudador().vida_actual` y `len(servicio.mapaConocido().salas)` (o `None` si no hay mapa) y llamar a `mostrar_fin_partida`; el banner `¡HAS MUERTO!` / `¡HAS LLEGADO…!` y el orden actual (puntaje, log, mensajes) se conservan; (e) cambiar cada `print` de rechazo o error por el catálogo de T034. **No cambiar** `_mapear_entrada_a_evento` ni la sintaxis de ningún comando. (FR-306, FR-307, FR-309, FR-310, FR-312, FR-313)
- [X] T037 [US2] Corregir los textos con caracteres dañados de `main.py` (FR-308): sustituir cada secuencia `Ã¡ Ã© Ã­ Ã³ Ãº Ã± Â§ â€¦` por la letra correcta en los mensajes de `reproducir`, de `mostrar_reporte`, de `--cache-size`, de `--hasta` y de los textos de ayuda de `argparse` (por ejemplo `ReproducciÃ³n terminada` → `Reproducción terminada`, `tamaÃ±o de la cachÃ©` → `tamaño de la caché`, `catÃ¡logo` → `catálogo`, `Â§5.1` → `§5.1`), guardando el archivo en UTF-8 sin cambiar nada más. Comprobar con una búsqueda de `Ã` y `Â` en `main.py` (debe dar 0 resultados) y que `tests_labs/prueba_reporte_solicitudes.py` (T014), `test_cli_checkpoint.py` y `test_replay_hasta.py` pasan. (FR-308, FR-310)

**Punto de control**: T006 a T008, T014 y T028 a T031 en verde; toda la suite en verde salvo lo anotado en T001.

---

## Fase 6: Medición (constitución VII)

**Propósito**: bloque `--bench pantallas` con su alternativa descartada y repetición de `--bench ciclo`.

- [X] T038 [P] Escribir `bench/pantallas.py` (contrato `contracts/bench-pantallas.md`): sección A, sala con 0, 10 y 100 enemigos (y objetos en proporción) con la **elegida** (`texto_sala`, lista + `join`) y la **alternativa descartada** (`texto_sala_concatenado`, concatenar con `+=`, definida solo en este archivo); sección B, resumen final, elegida y descartada; sección C, ayuda (informativo); verificaciones previas con `verificar(...)`: el texto elegido es **idéntico** al descartado en cada tamaño y dos construcciones dan el mismo texto; criterios duros: sala con 100 enemigos < 20 ms (mediana y máximo) y textos idénticos; razón de tiempos solo informa. Datos sintéticos deterministas (`bench.datos.SEMILLA`), sin red ni vista, sin dict/set/sorted. Devuelve `False` si un criterio duro falla. (constitución VII, FR-311, FR-316)
- [X] T039 Registrar el bloque en `bench/__init__.py`: importar `pantallas`, añadir `("pantallas", pantallas.ejecutar)` a `BLOQUES`, incluir `pantallas` en el texto de ayuda de `--bench` de `main.py` y agregar la frase final `Pantallas: CUMPLE.` / `NO CUMPLE` y el código de salida distinto de 0 si falla, siguiendo el patrón de `ir_a` y `llaves`. (constitución VII)
- [X] T040 [P] Escribir `bench/test_bench_pantallas.py` (como `bench/test_bench_historia.py`): el bloque corre en una carpeta temporal sin red, produce las filas de elegida y descartada para 0, 10 y 100 enemigos, y los criterios duros cumplen. (constitución VII, IX)
- [X] T041 Ejecutar `python main.py --bench pantallas` y `python main.py --bench ciclo` y copiar las cifras a `DECISIONES.md` (sección «011», con enlaces a `spec.md` y `plan.md`): la tabla elegida/descartada y el antes/después del ciclo (comparar con T002); indicar si la decisión final coincide con el plan. El ciclo debe seguir bajo 20 ms; si no, parar y documentar. (constitución VII, FR-316)

---

## Fase 7: Pulido y revisiones finales

- [X] T042 [P] Actualizar `README.md` (FR-314, SC-308): (a) los argumentos nuevos `--verificar <cripta>` y `--forzar` con sus códigos de salida 0, 1 y 2 y un ejemplo de cada uno (reemplazando la frase de la línea 25 que dice que «las opciones --verificar y --forzar las conecta la capacidad de Fernanda»); (b) el comando de **instalación de spec-kit con la versión fija** (la de `.specify/init-options.json`, `1.2.6`, en lugar del «1.2.3 o superior» actual de la tabla de requisitos), copiando el comando exacto que usa el equipo y comprobándolo; (c) cómo ejecutar las pruebas de aceptación: `python -m unittest test_arranque_verificado test_pantallas_texto test_pantallas_controlador test_pantallas_aislamiento -v` y la suite completa; (d) el comando `ayuda` y `--bench pantallas`.
- [X] T043 [P] Actualizar `DECISIONES.md` con las decisiones D1 a D8 de `research.md`, el resultado de T041 y el enlace a `spec.md` y `plan.md`; y `DOCUMENTACION_API.md` solo en lo que cambió en el servicio (T017). (constitución VII, flujo de desarrollo)
- [X] T044 [P] Registrar en **`PROMPTS_LLM_Fer.md`**, el archivo por integrante que ya usa el grupo (también existen los de JP y Scott; práctica por confirmar con Cesar, y si prefiere un solo archivo las filas se pasan a `PROMPTS_LLM.md` al final; hallazgo C1), los comandos `/speckit` con texto propio de esta capacidad que falten: la fila 18 para `/speckit-tasks` ya queda agregada con este archivo; añadir las filas siguientes para `/speckit-analyze` e `/speckit-implement` cuando se ejecuten, con fecha, herramienta (Claude Code) y modelo. (constitución XI)
- [X] T045 Revisar el cumplimiento de la **constitución I** en los archivos nuevos y tocados (`main.py`, `Controlador/Pantallas.py`, `Controlador/Vista.py`, `Controlador/ControladorJuego.py`, `Servicio/EstadoJuegoServicio.py`, `bench/pantallas.py`, `bench/__init__.py` y las pruebas nuevas): buscar con `Grep` `\bdict\(|\bset\(|\{\s*\}|sorted\(|\.sort\(|heapq|bisect|collections|networkx|OrderedDict|defaultdict|Counter` y revisar cada coincidencia (un `{}` o `dict` solo es válido para leer JSON); anotar el resultado y las excepciones justificadas en `specs/011-arranque-verificado-pantallas/research.md`, sección «Revisión de importaciones prohibidas», **antes** de dar la capacidad por terminada. (FR-316, constitución I)
- [X] T046 [P] Comprobar que **no cambió** el formato de guardado ni el log (FR-304, FR-315, SC): guardar una partida y comparar con una de antes del cambio (formato 8 / estado 5); ejecutar `test_persistencia_v7.py`, `test_replay_hasta.py`, `test_determinismo_replay.py` y `test_sin_red.py` (sin solicitudes nuevas, FR-316); ejecutar dos veces la misma partida y comparar `partida.log` (determinismo, constitución II).
- [X] T047 Ejecutar la guía `specs/011-arranque-verificado-pantallas/quickstart.md` completa (pruebas, pasos a mano de la sección 2 y 3, medición) y completar la tabla requisito → escenario → prueba sin huecos; ejecutar la suite completa y dejar el resultado en el mensaje de la confirmación final. (constitución IX)

---

## Dependencias y orden de ejecución

- **Fase 1** sin dependencias; **T003** (spec) se confirma antes de cualquier código.
- **Fase 2** depende de la fase 1 (T001, T004, T005); sus tareas son paralelas entre sí; **T016** cierra la fase y debe terminar **antes** de T035 (tocar la vista).
- **Fase 3** depende de la fase 2; T017 y T018 bloquean US1 y US2.
- **Fase 4 (US1)** y **Fase 5 (US2)** dependen de la fase 3 y se implementan juntas (misma prioridad). Choques: ambas tocan `main.py` (T024, T025, T037) y `ControladorJuego.py` (T026, T027, T036): se hacen **en ese orden**, no en paralelo.
- **Fase 6** depende de T032 y T033 (`texto_sala`, `texto_fin_partida`).
- **Fase 7** al final; T045 es la última revisión de código y T047 la última tarea.

### Orden entre las tareas de una historia

Pruebas (fallan) → servicio/utilidades → `main.py` → controlador → vista → verificación.

## Oportunidades de paralelismo

- Fase 1: T002, T004 y T005 en paralelo.
- Fase 2: T006 a T015 en paralelo (archivos distintos).
- Fase 3: T018 y T019 en paralelo; T017 antes de las historias.
- US1: T020 a T023 en paralelo (mismo archivo de pruebas: se escriben por bloques separados y se integran en una sola confirmación).
- US2: T028 a T031 en paralelo; T032 a T034 en el mismo archivo, en orden.
- Fase 6: T038 y T040 en paralelo.
- Fase 7: T042, T043, T044 y T046 en paralelo.

## Estrategia de implementación

Las dos historias son P1 y se entregan juntas, por lo que no hay un MVP parcial: aun así, el primer corte probable es **fase 1 → 2 → 3 → US1** (el arranque verificado ya cumple el enunciado §7.3 por sí solo), y después **US2**, medición y pulido. No se avanza de fase sin el punto de control en verde. Si una prueba existente falla por un motivo que no anuncia T016, se detiene y se corrige primero la especificación (principio X).

## Cobertura de requisitos

| Requisito | Tareas |
|---|---|
| FR-301 | T017, T021, T026, T027, T010 |
| FR-302 | T020, T024, T013, T009 |
| FR-303 | T021, T024, T025, T026 |
| FR-304 | T021, T023, T027 |
| FR-305 | T022, T025, T026 |
| FR-306 | T003, T006, T007, T028, T032, T035, T036 |
| FR-307 | T029, T033, T036, T017 |
| FR-308 | T005, T030, T034, T037, T014 |
| FR-309 | T004, T018, T030, T033, T036 |
| FR-310 | T005, T008, T018, T034, T036 |
| FR-311 | T018, T028, T032, T038 |
| FR-312 | T006, T011, T019, T035, T036 |
| FR-313 | T004, T008, T012, T031, T036 |
| FR-314 | T042 |
| FR-315 | T009, T023, T046 |
| FR-316 | T019, T038, T045, T046 |
| FR-317 | T001, T006 a T016 |
