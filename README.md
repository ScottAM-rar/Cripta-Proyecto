
# Cesar Segura Galeano
# Jose Pablo Sánchez Ramírez
# Aharam Scott Alvarado Marchena
# Fernanda Alfaro 

# Cripta-Proyecto
Proyecto 1 de Estructura de datos

   Python 3.11+. Instalar: pip install requests
   Jugar: python main.py
   Sin conexión: python main.py --offline (requiere haber descargado la cripta antes)
   Reproducir: python main.py --replay NOMBRE.log (los logs quedan en logs/)
   Reproducir hasta un instante: python main.py --replay NOMBRE.log --hasta T
     (reproduce solo los eventos con tiempo virtual <= T y muestra el estado exhaustivo en ese instante)
   Mediciones: python main.py --bench
   Mediciones de terreno y cazador: python main.py --bench terreno
   Mediciones del recorrido por niveles: python main.py --bench recorrido
   Capacidad 009 (ubicación de llaves): python main.py --bench llaves; la consulta de llaves cuenta en el conteo de solicitudes (1 la primera partida, 0 con las llaves ya guardadas con la misma versión y en --offline)
   Mediciones de reproduccion acotada: python main.py --bench replay
   Puntos de control: python main.py --checkpoint-cada K (una instantánea cada K acciones del jugador; por defecto 10); mediciones: python main.py --bench puntos_control
   Consultar el pasado durante la partida (o al terminar): escribir historia <t> (estado en el instante virtual t) o historia #k (estado justo antes de tu acción k); no consume tiempo, no cuenta como acción ni queda en el log. Mediciones: python main.py --bench historia
   Capacidad 003 (verificación de resolubilidad: si la cripta se puede completar con las llaves obtenibles; una partida nueva no inicia en una cripta no resoluble salvo con forzar): python main.py --bench resolubilidad; las opciones --verificar y --forzar las conecta la capacidad de Fernanda sobre esta interfaz (EstadoJuegoServicio.verificar e iniciarJuego(..., forzar))
   Pruebas: python -m unittest discover -p "test_*.py"
   Pruebas de replay acotado: python -m unittest test_replay_hasta test_determinismo_replay test_rendimiento_replay
   Datos generados: datos_cripta/, logs/, Partidas Guardadas/

## Desarrollo guiado por especificaciones (Parte II)

Capacidades (cada una en `specs/<NNN-nombre>/`): `001-terreno-y-cazador` (costo de las salidas y enemigo cazador); `005-recorrido-por-niveles` (visitar las salas en orden de cercanía; por ahora solo se construye y se mide: la precarga y la verificación de resolubilidad lo adoptarán después); `007-puntos-de-control` (instantáneas periódicas de la partida cada K acciones, con el pergamino recortando la línea de tiempo); `008-replay-hasta` (reproducir una partida grabada hasta el instante t: `python main.py --replay NOMBRE.log --hasta T`); `004-linea-de-tiempo` (los comandos `historia <t>` e `historia #k`, que reconstruyen un estado pasado desde el punto de control más cercano sin tocar la partida en curso). Las decisiones y su comparación con el plan original están en `DECISIONES.md`; los comandos de Spec Kit con texto propio, en `PROMPTS_LLM.md`.

**Compatibilidad de partidas guardadas**: el formato binario está en la versión 7 (puntos de control y línea de tiempo; la capacidad 004 no lo cambia). Antes subió de la versión 5 a la 6 (costo por salida y rango por enemigo). Un archivo de una versión anterior se rechaza con un mensaje que indica la versión encontrada y la esperada; no se migra.

Para la Parte II se usa **GitHub Spec Kit** con los agentes **Claude Code** y **Antigravity**.

| Herramienta | Versión |
|---|---|
| Spec Kit (`specify-cli`) | **1.2.3 o superior** |
| Agente 1 | Claude Code |
| Agente 2 | Antigravity |
| Python | 3.11+ |

Instalación (todo el equipo debe usar exactamente esta versión):

```bash
  # debe mostrar 1.2.3
```

Al clonar el repositorio no hace falta ejecutar `specify init`: la carpeta `.specify/` y los comandos `/speckit.*` ya están versionados.
