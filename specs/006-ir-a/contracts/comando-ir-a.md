# Contrato: comando «ir a» (controlador y vista)

**Requisitos**: FR-231, FR-237, FR-238, FR-243, FR-249. **Principio IV**: el controlador solo interpreta; la vista solo imprime.

## 1. Sintaxis

```text
ir a <id de sala>
```

- Mayúsculas y espacios sobrantes no importan; el id es un entero.
- Se agrega a la ayuda del turno: `... mapa, ir a <sala>, historia ...`.
- Un id que no es entero se rechaza en el controlador con «El destino debe ser el número de una sala.», **sin llamar al servicio** (no hay orden que el modelo pueda rechazar).

## 2. Flujo

1. El controlador compara la entrada **antes** de `_mapear_entrada_a_evento` (igual que `mapa` e `historia`).
2. Llama a `servicio.irA(destino)`.
3. Pasa el `ResultadoViajeDTO` a `Vista.mostrar_viaje(resultado)`.
4. El bucle del turno continúa: al empezar la siguiente vuelta pinta la sala actual como siempre.

Si la partida terminó durante el viaje (`MUERTE`), el bucle sigue el camino habitual de fin de partida.

## 3. Lo que muestra la vista

| Estado | Salida |
|---|---|
| `RECHAZADO` | Una línea con el mensaje del motivo. Nada más |
| `LLEGADO` | «Llegaste a la sala N tras P pasos (tiempo T).» |
| `DETENIDO` | El mensaje del motivo y «Te detuviste en la sala N tras P pasos (tiempo T).» |

El texto de cada motivo es el de la tabla de [data-model.md](../data-model.md). Los mensajes de la bitácora que el flujo normal ya produce durante los pasos (daño, activaciones, trampas) se muestran como siempre en `ultimosMensajes`.

## 4. Lo que el comando NO es

- No es un evento del reloj y no pasa por `accionJugador` como orden; los **pasos** sí.
- No cuenta como acción para el pergamino cuando se rechaza (FR-238); cuando se acepta, cada paso cuenta como una.
- No es un `EventoDTO` nuevo.

## 5. Pruebas

`test_viaje_comando.py`: con entradas simuladas, `ir a 7` hacia una sala no explorada imprime el motivo y deja el reloj igual (**B-N1**); `ir a x` no llama al servicio; un viaje completo imprime el resumen.
