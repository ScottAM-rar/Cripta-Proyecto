## 1. Revisión de `ObjetoLogica`

**Prompts para copilot**

- Revisa si los métodos y los casos de `ObjetoLogica` están correctos.
- Comprueba el uso de pociones, objetos consumibles y equipamiento.
- Busca inconsistencias entre el inventario, el objeto actual y el jugador.

**Objetivo**

Validar que cada tipo de objeto tuviera un flujo completo: localizarlo, consumirlo o equiparlo, producir el resultado del evento y registrar lo necesario para deshacerlo.

---

## 2. Diseño de `CambioDTO` y agrupación de acciones

**Prompts para copilot**

- Basado en `DeltaDTO`, crea un `CambioDTO` con los siguientes atributos: `tipo_accion`, `objeto_afectado` y `valor_anterior`.
- Sustituye en el código lo que utilizaba `DeltaDTO` por `CambioDTO` para evitar errores al intercambiarlo y explica cómo implementarlo correctamente en los métodos existentes.
- Recomienda una manera de guardar dos cambios en una sola acción, ya que las pociones deben restaurar tanto la eliminación del inventario como la vida o el modificador de velocidad.

**Objetivo**

Establecer un contrato claro para el nuevo DTO de cambios reversibles y permitir que una acción afecte a varios objetos o atributos.

---

## 3. Correcciones generales

**Prompts para copilot**

- Revisa `InventarioLogica` y busca por qué no se actualiza el valor de `actual`.
- Revisa que `iniciar_accion`, `pop` y `descartar_accion` funcionen como se espera.
- Verifica que las acciones anteriores se eliminen completamente al superar el límite de cinco.

**Objetivo**

Garantizar el correcto funcionamiento y la depuración de errores.


---

## 4. Revisión de todos los `case` de `PergaminoLogica`

**Prompts para copilot**

- Revisa todos los casos de reversión.
- Comprueba movimiento, recoger, soltar, equipar, desequipar y uso de objetos.
- Revisa puerta, trampa, reloj, agenda, puntaje, enemigos, último paso y bitácora.
- Verifica qué hacer con un tipo de acción desconocido.

**Objetivo**

Asegurar que cada acción registrada tenga una operación inversa coherente y que los casos incompletos no produzcan retrocesos silenciosamente incorrectos.

---

## 5. Errores de inventario al equipar y restaurar

**Prompts para copilot**

- Revisa el equipamiento de un arma cuando ya hay otra arma y una armadura equipada.
- Analiza fallos al usar un arma que no estaba en el cursor actual.
- Revisa `mostrar_equipado_1`, `mostrar_equipado_2`, inserción por índice y restauración.

**Objetivo**

Hacer compatible el inventario doblemente enlazado con el modelo de dos posiciones equipadas y con el cursor de navegación del jugador.

---

## 6. Revisión de llamadas entre clases

**Prompts para copilot**

- Comprueba si todos los usos de metodos en `InventarioLogica` son correctos y estan bien implementados.
- Revisa también `JugadorLogica`, `ObjetoLogica`, `PergaminoLogica` y `RetrocesoLogica` en busca de lo mismo, comprobar si los metodos son correctamente utilizados e implementados.
- Busca llamadas a métodos eliminados o nombres antiguos.
- Busca codigo muerto como `deshacer_accion` que no ya no tenia sentido.

**Objetivo**

Detectar errores de integración después de cambiar nombres, separar responsabilidades o sustituir la implementación anterior. Tambien eliminar codigo muerto.


---

## 7. Bitácora como lista enlazada

**Prompts para copilot**

- Convierte `BitacoraLogica` en una lista enlazada con comportamiento FIFO y capacidad fija.

**Objetivo**

BitacoraLogica antes utilizaba un vector, se convirtio a lista enlazada.

---

## 8. Tiempo del reloj y eventos de enemigos

**Prompts para copilot**

- Revisa si los `CambioDTO` guardan el tiempo correcto.
- Haz que cada evento del gestor genere una nueva acción cuando corresponda.
- Busca porque hay eventos duplicados al retroceder.
- Determina si el reloj debe retroceder y cómo podria restaurar su agenda.

**Objetivo**

Integrar el retroceso lógico con el reloj virtual y su agenda de eventos sin duplicar enemigos, trampas o eventos futuros.


---

## 9. Pruebas y depuración del flujo completo

**Prompts para copilot**

- Prueba todos los métodos de `PergaminoLogica`.
- Agrega pruebas visuales.
- Revisa los casos que fallan y porque fallan.

**Objetivo**

Pasar de revisiones aisladas a pruebas unitarias, de integración y de ejecución real.


---
