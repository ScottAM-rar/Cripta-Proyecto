# Contrato: marcas del viaje en el log y reproducción

**Requisito**: FR-252. **Decisión**: [research.md](../research.md) D6.

## 1. Marcas

Dos tipos nuevos de registro informativo, `TIPOS_MARCA_VIAJE = ("IR_A", "FIN_IR_A")`, con el mismo estilo que el registro de cursor de inventario (costo 0, no es evento del reloj ni acción):

```json
{"tipo_accion": "IR_A", "tiempo_ejecucion": 0, "actor": {"tipo": "jugador"}, "datos_extra": [<destino>]}
{"tipo_accion": "FIN_IR_A", "tiempo_ejecucion": 0, "actor": {"tipo": "jugador"}, "datos_extra": ["<estado>", "<motivo o ninguno>", <sala_final>]}
```

Entre ellas van, **tal cual los escribe el flujo normal**, los registros `MOVER_JUGADOR` de los pasos. Ejemplo (viaje de 2 pasos que llega):

```text
IR_A            destino 9
MOVER_JUGADOR   sala 1 → este
MOVER_JUGADOR   sala 2 → norte
FIN_IR_A        LLEGADO, ninguno, sala 9
```

Un viaje cancelado por pergamino: tras los pasos y el registro del propio pergamino, `FIN_IR_A  DETENIDO, PERGAMINO, <sala tras revertir>`. Un comando rechazado **no** escribe nada.

## 2. Quién las escribe y quién las lee

| Quién | Qué hace |
|---|---|
| `ViajeLogica` | Escribe `IR_A` al aceptar y `FIN_IR_A` al terminar o cancelarse, por la misma ruta que ya usa el cursor de inventario (`LogEventos.registrar_marca`, y al archivo `partida.log` a través del registrador) |
| Repetición completa (`_repetirPartidaInterno`) | Salta `IR_A`; en `FIN_IR_A` comprueba que el jugador está en la sala final anotada, si no `ValueError("La reproducción no es fiel: ...")` |
| Repetición hasta un instante o acción | Igual, pero no comprueba si el corte cae antes de llegar a `FIN_IR_A` |
| Pasadas 1 y 2 de los segmentos (puntos de control) | Saltan ambas marcas sin ejecutar ni contar nada |
| `historia #k` | No ve las marcas: cuenta acciones, y los pasos son acciones |

Los cuatro puntos que hoy comparan con `TIPOS_CURSOR_INVENTARIO` pasan a reconocer también `TIPOS_MARCA_VIAJE` (un `continue` sin ejecutar). Ninguna otra ruta del log cambia.

## 3. Garantías

- **Pasos = movimientos**: repetir un viaje es repetir sus movimientos; `acciones_linea_tiempo`, los puntos de control y `replay hasta` son los de siempre.
- **El pergamino** que cancela un viaje queda en el log como cualquier otro, antes de `FIN_IR_A`.
- **Sin cambio de formato**: son cadenas de la misma lista; el guardado binario no se toca (formato 8, estado 5).

## 4. Pruebas

`test_viaje_registro.py`: (1) el log de un viaje lleva exactamente `IR_A`, los pasos y `FIN_IR_A`, en ese orden; (2) repetir el log da el mismo estado; (3) un log con `FIN_IR_A` cuya sala final no coincide falla como «no es fiel»; (4) `historia #k` y `replay hasta` a mitad de un viaje dan el estado de caminar a mano esos pasos; (5) guardar y cargar con un viaje ya hecho no cambia nada.
