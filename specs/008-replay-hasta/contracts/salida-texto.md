# Contrato de Interfaz de Presentación: Salida de Texto

Define el formato exacto del texto que `main.py` emite en la salida estándar (`stdout`) para las ejecuciones de reproducción.

---

## 1. Reproducción acotada (`--replay <PARTIDA.log> --hasta <t>`)

La función `reproducir()` en `main.py` formatea los datos contenidos en `ResultadoReplayHastaDTO` cumpliendo FR-404.

### 1.1 Caso estándar (reproducción acotada exitosa, partida en curso)

Cuando la reproducción se detiene en o antes de $t$ y la partida no ha concluido:

```text
Reproducción hasta t={tope} terminada.
Instante virtual alcanzado: {instante_alcanzado}
Acciones del jugador reproducidas: {acciones_reproducidas}
Estado del jugador:
  Sala actual: {id_sala_jugador}
  Puntos de vida: {vida_jugador}
  Llaves: {lista_llaves o "(ninguna)"}
  Objetos: {lista_objetos o "(ninguno)"}
Enemigos en la sala:
  - {nombre_enemigo_1}: {vida_1} PV
  - {nombre_enemigo_2}: {vida_2} PV
  (o "(ninguno)" si la sala no contiene enemigos vivos)
Estado de la partida: En curso (no ha terminado).
```

### 1.2 Caso de terminación anticipada por fin de partida (muerte o victoria)

Si el jugador muere (o gana) en un instante $t_{muerte} \le t$:

```text
Reproducción hasta t={tope} terminada.
Instante virtual alcanzado: {instante_alcanzado}
Acciones del jugador reproducidas: {acciones_reproducidas}
Estado del jugador:
  Sala actual: {id_sala_jugador}
  Puntos de vida: {vida_jugador}
  Llaves: {lista_llaves o "(ninguna)"}
  Objetos: {lista_objetos o "(ninguno)"}
Enemigos en la sala:
  - {nombre_enemigo}: {vida} PV
Estado de la partida: Terminada antes de alcanzar t={tope}.
  Motivo: {motivo_terminacion}
```

### 1.3 Caso de log agotado antes de $t$ (FR-405)

Si el archivo de registro se termina en un instante menor a $t$ sin que la partida haya concluido:

```text
Aviso: el log terminó en el instante {instante_alcanzado} antes de alcanzar t={tope}.

Reproducción hasta t={tope} terminada.
Instante virtual alcanzado: {instante_alcanzado}
Acciones del jugador reproducidas: {acciones_reproducidas}
Estado del jugador:
  Sala actual: {id_sala_jugador}
  Puntos de vida: {vida_jugador}
  Llaves: {lista_llaves o "(ninguna)"}
  Objetos: {lista_objetos o "(ninguno)"}
Enemigos en la sala:
  (ninguno)
Estado de la partida: En curso (el log no contenía más acciones).
```

### 1.4 Caso con $t = 0$ (FR-406)

No se ejecuta ninguna acción del registro y se exhibe el estado inicial del jugador y la sala de entrada:

```text
Reproducción hasta t=0 terminada.
Instante virtual alcanzado: 0
Acciones del jugador reproducidas: 0
Estado del jugador:
  Sala actual: {id_sala_inicial}
  Puntos de vida: {vida_inicial}
  Llaves: (ninguna)
  Objetos: (ninguno)
Enemigos en la sala:
  (ninguno)
Estado de la partida: En curso (estado inicial previo al juego).
```

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
