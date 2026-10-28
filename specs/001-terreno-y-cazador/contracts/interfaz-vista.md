# Contrato de interfaz: qué muestra la vista

La vista solo presenta; no calcula ni decide.

| Requisito | Qué se muestra |
|---|---|
| FR-130 | Cada salida de la sala actual con su costo, junto a destino y estado de la puerta. Ejemplo: `> Norte -> Sala 8 [Abierta] costo 250` |
| FR-131 | Cada enemigo con una marca visible si es cazador, distinta de la de los demás tipos. Ejemplo: `- [CAZADOR] Sabueso (Vida: 10/10)` |
| Advertencias de datos | Al iniciar, las advertencias de costos o rangos inválidos, una por línea |

Los modos `--replay`, `--bench` y `--verificar` no instancian la vista (principio IV).
