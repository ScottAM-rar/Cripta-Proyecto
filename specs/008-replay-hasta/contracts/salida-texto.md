# Contrato de Interfaz de Presentación: Salida de Texto

Define el formato exacto del texto que `main.py` emite en la salida estándar (`stdout`) para las ejecuciones de reproducción.

---

## 1. Reproducción acotada (`--replay <PARTIDA.log> --hasta <t>`)

La función `reproducir()` en `main.py` formatea los datos de `ResultadoReplayHastaDTO` cumpliendo FR-404. Toda la información proviene del DTO; el mapa conocido no se imprime hasta que exista la capacidad de niebla de guerra.

### 1.1 Bloque común de estado

```text
Reproducción hasta t={instante_pedido} terminada.
Instante virtual alcanzado: {instante_alcanzado}
Acciones del jugador reproducidas: {acciones_reproducidas}
Estado del jugador:
  Sala actual: {id_sala_jugador}
  Puntos de vida: {vida_jugador}
  Estadísticas: ataque {ataque_jugador}, defensa {defensa_jugador}, velocidad {velocidad_jugador}
  Efectos activos: {lista_efectos o "(ninguno)"}
  Llaves: {lista_llaves o "(ninguna)"}
  Objetos: {lista_objetos o "(ninguno)"}
Enemigos en la sala:
  - {nombre} ({id_instancia}): {vida} PV
  (o "  (ninguno)" si la sala no contiene enemigos vivos)
```

Esta cabecera y este bloque se imprimen siempre. Las líneas finales dependen del caso.

### 1.2 Partida en curso

Cuando la reproducción se detiene en el instante pedido, o en el último evento anterior a él, y la partida no ha concluido:

```text
Estado de la partida: En curso (no ha terminado).
```

### 1.3 Partida terminada

Si el jugador muere o gana (`partida_terminada`):

- Con `instante_alcanzado < instante_pedido`:
```text
Estado de la partida: Terminada antes de alcanzar t={instante_pedido}.
  Motivo: {motivo_terminacion}
```
- Con `instante_alcanzado == instante_pedido`, sin el aviso de «antes de alcanzar»:
```text
Estado de la partida: Terminada en t={instante_pedido}.
  Motivo: {motivo_terminacion}
```

### 1.4 Log agotado antes de t (FR-405)

Si el registro se termina con el reloj estrictamente antes de $t$ sin que la partida haya concluido, se antepone el aviso y el bloque común se imprime con el estado final:

```text
Aviso: el log terminó en el instante {instante_alcanzado} antes de alcanzar t={instante_pedido}.

(bloque común de 1.1)
Estado de la partida: En curso (el log no contenía más acciones).
```

### 1.5 Caso con t = 0 (FR-406)

No hay regla especial: la primera decisión del jugador corresponde al instante 0 y no se ejecuta. Se imprime el bloque común con `Instante virtual alcanzado: 0`, `Acciones del jugador reproducidas: 0` y el estado inicial real (sala, vida, estadísticas, efectos, llaves, objetos y enemigos de la sala de entrada, según el log), seguido de `Estado de la partida: En curso (no ha terminado).`

---

## 2. Preservación estricta de `--replay` sin `--hasta` (FR-409)

Cuando se invoca `--replay <PARTIDA.log>` sin el parámetro `--hasta`, la salida conserva con exactitud el formato de la Parte I:

```text
Reproducción terminada: {total_acciones} acciones del jugador.
Estado final: {motivo}
```
o
```text
Reproducción terminada: {total_acciones} acciones del jugador.
La partida no había terminado al acabarse el log.
```

Seguido únicamente del bloque de reporte de solicitudes de red/caché si corresponde.
