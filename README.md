
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
   Mapa conocido (capacidad 002, niebla de guerra): escribir mapa; muestra solo lo que el jugador conoce (salas exploradas, avistadas, y la última observación de cada puerta) y no consume tiempo ni cuenta como acción. Mediciones: python main.py --bench mapa
   Viajar a una sala ya explorada (capacidad 006): escribir ir a <id de sala>; el personaje camina por la ruta más barata que conoce, un paso por vez, y se detiene si una puerta recordada abierta resulta cerrada y no hay otra ruta, al despertar enemigos, ante un enemigo activo, al recibir daño o al morir; una orden que no se puede cumplir (sala no explorada, sin ruta conocida) se rechaza sin consumir tiempo. Mediciones: python main.py --bench ir_a
   Capacidad 003 (verificación de resolubilidad: si la cripta se puede completar con las llaves obtenibles): python main.py --bench resolubilidad
   Capacidad 011 (arranque verificado y pantallas claras): al iniciar una partida nueva se muestra el reporte de resolubilidad de la cripta, sea o no resoluble, antes del primer turno.
     Verificar una cripta sin jugar: python main.py --verificar CRIPTA (muestra el reporte y termina; no abre partida, ni log, ni vista). Código de salida: 0 resoluble, 1 no resoluble, 2 error de uso o de lectura (cripta inexistente, datos no disponibles, argumento faltante). No se combina con --replay ni con --bench.
     Jugar una cripta no resoluble: python main.py --forzar (se muestra el reporte y una advertencia, y la partida se abre). Sin --forzar, una cripta no resoluble se rechaza, el programa dice qué hacer y sale con código 1. --forzar no se guarda en partida.log ni en el estado guardado.
     En la partida: escribir ayuda muestra todos los comandos con su sintaxis (no consume tiempo ni cuenta como acción). Cada turno muestra siempre las mismas secciones, en el mismo orden: sala, salidas (dirección, costo y estado: abierta, cerrada o sin observar), enemigos (activos o dormidos), objetos, trampas, estado del jugador (vida, tiempo, antorcha), inventario y últimos mensajes. Al terminar, un resumen con motivo, puntaje, acciones, tiempo, vida final y salas exploradas. Mediciones: python main.py --bench pantallas
   Pruebas: python -m unittest discover -p "test_*.py"
   Pruebas de aceptación de la capacidad 011 (arranque verificado y pantallas): python -m unittest test_arranque_verificado test_pantallas_texto test_pantallas_controlador test_pantallas_aislamiento bench.test_bench_pantallas -v
   Pruebas de replay acotado: python -m unittest test_replay_hasta test_determinismo_replay test_rendimiento_replay
   Datos generados: datos_cripta/, logs/, Partidas Guardadas/

## Desarrollo guiado por especificaciones (Parte II)

Capacidades (cada una en `specs/<NNN-nombre>/`): `001-terreno-y-cazador` (costo de las salidas y enemigo cazador); `002-niebla-de-guerra` (mapa conocido: salas exploradas, avistadas o desconocidas y memoria de las puertas; comando `mapa`); `005-recorrido-por-niveles` (visitar las salas en orden de cercanía; por ahora solo se construye y se mide: la precarga y la verificación de resolubilidad lo adoptarán después); `007-puntos-de-control` (instantáneas periódicas de la partida cada K acciones, con el pergamino recortando la línea de tiempo); `008-replay-hasta` (reproducir una partida grabada hasta el instante t: `python main.py --replay NOMBRE.log --hasta T`); `004-linea-de-tiempo` (los comandos `historia <t>` e `historia #k`, que reconstruyen un estado pasado desde el punto de control más cercano sin tocar la partida en curso); `006-ir-a` (el comando `ir a <id>`, que viaja hasta una sala explorada por la ruta más barata del mapa conocido). Las decisiones y su comparación con el plan original están en `DECISIONES.md`; los comandos de Spec Kit con texto propio, en `PROMPTS_LLM.md`.

**Compatibilidad de partidas guardadas**: el formato binario está en la versión 8 (conocimiento del jugador de la niebla de guerra; la versión 7 añadió los puntos de control y la línea de tiempo, y la capacidad 004 no la cambia). Antes subió de la versión 5 a la 6 (costo por salida y rango por enemigo). Un archivo de una versión anterior se rechaza con un mensaje que indica la versión encontrada y la esperada; no se migra.

Para la Parte II se usa **GitHub Spec Kit** con los agentes **Claude Code** y **Antigravity**.

| Herramienta | Versión |
|---|---|
| Spec Kit (`specify-cli`) | **1.2.6** (la versión con la que se generó `.specify/`, ver `.specify/init-options.json`) |
| Agente 1 | Claude Code |
| Agente 2 | Antigravity |
| Python | 3.11+ |

Instalación (todo el equipo debe usar exactamente esta versión):

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.2.6
specify version
# debe mostrar 1.2.6
```

Al clonar el repositorio no hace falta ejecutar `specify init`: la carpeta `.specify/` y los comandos `/speckit.*` ya están versionados.
