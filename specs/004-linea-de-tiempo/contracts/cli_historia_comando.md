# Contrato de Interfaz: Comando Interactivo `historia`

**Capacidad**: `004-linea-de-tiempo`  
**Capa**: Controlador y Vista (`Controlador/ControladorJuego.py`, `Controlador/Vista.py`)  
**Fecha**: 2026-11-08  

---

## 1. Sintaxis Aceptada

El comando se ingresa en el prompt interactivo de la partida viva y en el bucle posterior a la finalización de la partida.

### 1.1 Consulta por instante de reloj:
- `historia <t>` (p. ej., `historia <120>`, `historia <0>`)
- `historia t` (p. ej., `historia 120`, `historia 0`)
- No distingue mayúsculas/minúsculas: `HISTORIA 50`, `Historia <50>`.

### 1.2 Consulta por número de acción:
- `historia #k` (p. ej., `historia #1`, `historia #4`)
- `historia # k` (con espacio opcional tras el numeral)
- No distingue mayúsculas/minúsculas: `HISTORIA #2`.

---

## 2. Interceptación y Flujo de Control

1. **Punto de Interceptación**:
   - En `ControladorJuego.iniciar()`, la entrada del usuario se evalúa **antes** de llamar a `_mapear_entrada_a_evento()`.
   - El comando `historia` **NO** se convierte en `EventoDTO`, **NO** pasa por `accionJugador()`, **NO** se envía a la agenda del reloj y **NO** se registra en `partida.log`.
2. **Ciclo de Partida Viva**:
   - Tras responder a una consulta de historia (exitosa o con error), el bucle principal continúa en el mismo turno, mostrando el estado actual y solicitando la siguiente acción del jugador.
3. **Ciclo Post-Partida**:
   - Cuando la partida termina por muerte o victoria, tras mostrar el resumen final, el juego ofrece un sub-bucle interactivo que permite ingresar consultas de historia o `salir`.

---

## 3. Mensajes de Error en Consola

Los errores no lanzan excepciones no controladas a la consola ni terminan el programa:

| Caso | Entrada de Ejemplo | Salida en Pantalla |
|---|---|---|
| Instante futuro | `historia 9999` | `Error: El instante 9999 aún no ha ocurrido (reloj actual: <T>).` |
| Acción futura | `historia #50` | `Error: La acción #50 aún no ha ocurrido (acciones vigentes: <N>).` |
| Acción cero | `historia #0` | `Error: El número de acción debe ser mayor o igual que 1.` |
| Parámetro no numérico | `historia abc` | `Error: Parámetro de historia no reconocido. Usa 'historia <t>' o 'historia #k'.` |
| Número decimal | `historia 12.5` | `Error: El parámetro debe ser un número entero.` |
| Valor negativo | `historia -5` | `Error: El instante o número de acción no puede ser negativo.` |

---

## 4. Salida Formateada por la Vista (`VistaConsola.mostrar_historia`)

La vista presenta el estado histórico de forma estructurada según FR-431:

```text
==================================================
ESTADO HISTÓRICO: Instante <t> | Acción #<k>
==================================================
SALA: <id_sala>
VIDA: <vida>/<vida_max>
ESTADÍSTICAS: Ataque: <atk> | Defensa: <def> | Velocidad: <vel>

--- INVENTARIO ---
  Llaves: <llave_1>, <llave_2> (o 'Ninguna')
  Objetos: <obj_1>, <obj_2> (o 'Ninguno')

--- EFECTOS ACTIVOS ---
  <efecto_1>, <efecto_2> (o 'Ninguno')

--- ENEMIGOS EN LA SALA ---
  - <Nombre> (ID: <id_instancia>, Vida: <vida>)
  (o 'No había enemigos en esta sala')
==================================================
```

*(Nota sobre el mapa conocido: Si `resumen.mapa_conocido is None`, la sección de mapa se omite íntegramente de la salida).*
