# Cripta-Proyecto Estructura de Datos
```markdown
Cripta simula un juego de mazmorras guiado por un reloj virtual de eventos, combate por turnos, gestión avanzada de inventarios circulares, trampas dinámicas, sistema de guardado/carga y reproducción de partidas. El juego posee ciertas características principales como:

* Gestión de Criptas Dinámicas: El juego hace una selección de criptas (mundos) disponibles y carga bajo demanda mediante cliente HTTP y caché LRU.
* Reloj Virtual y Sincronización de Eventos: Las acciones del jugador y los enemigos consumen unidades de tiempo específicas, permitiendo que los monstruos actúen y las trampas se activen de forma asíncrona.
* Sistema de Inventario Circular: Posee una navegación fluida entre los objetos del inventario mediante punteros lógicos como: siguiente, anterior, usar, soltar.
* Persistencia y Reproducción (Replays): Se tiene una capacidad de guardar y cargar partidas en curso, además de registrar logs detallados para reproducir partidas anteriores.
* Tabla de Puntajes: Registro interactivo de los mejores puntajes al finalizar la aventura (ya sea por victoria al escapar o por derrota).

Para garantizar que el reloj virtual funcione correctamente y permita la interacción de enemigos y trampas, cada acción del jugador consume un costo base de tiempo estipulado:

| Acción | Costo / Tiempo de Ejecución |
| :--- | :--- |
| Moverse a una sala vecina (norte, sur, este, oeste) | 100 |
| Atacar a un enemigo | 100 |
| Usar un objeto del inventario | 50 |
| Abrir / Cerrar puerta (con o sin llave) | 50 |
| Armar / Activar trampa | 50 |
| Recoger / Soltar un objeto del suelo | 25 |

Para la instalación y configuración de Cripta se recomienda hacer los siguientes pasos:

1. **Clonar el repositorio:** 
```bash
git clone <url-del-repositorio>
cd Cripta-Proyecto
```
2. **Crear y activar un entorno virtual:** 
* **En Windows (PowerShell / CMD):** 
```bash
python -m venv venv
venv\Scripts\activate
``` 
* **En macOS / Linux:** 
```bash
python3 -m venv venv
source venv/bin/activate
```
3. **Instalar dependencias del proyecto:** 
```bash
pip install requests

```

---

Algunos comando de ejecución importantes para utilizar en medio del juego son los siguientes:

### 1. Modo Interactivo Normal
Para iniciar el juego de forma estándar (conectándose a la red y permitiendo elegir criptas, semillas o cargar partidas guardadas):
```bash
python main.py
```

### 2. Modo Offline (`--offline`)
Para jugar utilizando únicamente los datos y catálogos guardados en disco local, sin realizar solicitudes a la red: 
```bash
python main.py --offline
```

### 3. Modo de Reproducción de Partidas (`--replay`)
Para reproducir automáticamente un archivo de log grabado previamente sin requerir interacción del usuario: 
```bash
python main.py --replay <nombre_archivo.log>
``` 
*(El archivo de log debe estar ubicado obligatoriamente en la carpeta de registros).*

### 4. Pruebas de Rendimiento (`--bench`)
Para ejecutar pruebas de rendimiento sintéticas sobre los módulos del sistema (como caché, inventarios, ordenamiento, bitácoras, etc.): 
```bash
python main.py --bench todo
``` 
O bien, especificando bloques particulares separados por comas: 
```bash
python main.py --bench agenda,cache,inventario
``` 
Si deseas exportar los resultados de las pruebas directamente a un archivo CSV: 
```bash
python main.py --bench todo --bench-csv resultados_benchmark.csv
```

### 5. Configuración de Memoria Caché (`--cache-size`)
Para definir la cantidad de fichas del catálogo que se mantienen activas en memoria RAM (por defecto viene configurado): 
```bash
python main.py --cache-size 50
```

La ubicación de los archivos generados se encuentran durante la ejecución del programa, el sistema gestiona automáticamente los siguientes archivos y directorios en la raíz del proyecto: 
* **Logs de Partidas (`logs/`):** Al finalizar o registrar una partida, los archivos de historial cronológico (`.log`) se almacenan de manera predeterminada en la carpeta `logs/` para su posterior reproducción mediante `--replay`. 
* **Partidas Guardadas / Puntajes:** Los archivos de guardado rápido de partidas y la tabla de puntajes persistentes se almacenan localmente en el directorio de trabajo del proyecto configurado por la capa de adaptadores.

Guía para jugar cripta:

## Al ejecutar el programa mediante la terminal (`python main.py`), se presentarán las siguientes opciones previas al inicio formal de la exploración:
1. **Tabla de Puntajes:** El sistema te preguntará si deseas ver la tabla de puntajes histórica respondiendo con `s` (sí) o `n` (no).
2. **Carga de Partida:** Podrás elegir si deseas reanudar una partida guardada previamente ingresando el nombre del archivo de guardado.
3. **Selección de Cripta:** Si decides iniciar una nueva partida, se listarán las criptas disponibles obtenidas mediante el servicio. Deberás ingresar el número correspondiente a la cripta que deseas explorar.
4. **Semilla (Seed):** Se te solicitará una semilla numérica opcional. Si dejas el espacio en blanco, el juego generará una semilla aleatoria de manera automática.

En cada turno, se renderizará de manera limpia y estructurada la información actual de tu entorno:
- **Cabecera de Sala:** Nombre y número de identificación (ID) de la sala actual, junto con tu barra de vida actual y máxima (`VIDA JUGADOR`).
- **Salidas:** Listado de direcciones disponibles (`Norte`, `Sur`, `Este`, `Oeste`), indicando si se encuentran abiertas o cerradas (y si exigen alguna llave en particular).
- **Objetos en la Sala:** Elementos presentes en el suelo que puedes recolectar.
- **Enemigos:** Criaturas hostiles en la sala con su respectivo estado de salud actual.
- **Trampas:** Mecanismos de peligro presentes, su daño estimado y estado (armada o desarmada).
- **Inventario:** El objeto que posees seleccionado actualmente en tu inventario circular.

Durante tu turno, se desplegará el indicador de entrada solicitando tu jugada. Los comandos válidos que reconoce el controlador son los siguientes:

### Movimiento y Exploración
* **`norte`**, **`sur`**, **`este`**, **`oeste`**: Desplaza a tu personaje a una sala vecina a través de la salida indicada, solo debes de poner la dirección a la que quieres ir (Costo en el reloj virtual: **100** unidades de tiempo).

### Combate
* **`atacar`**: Inicia una acción ofensiva contra un enemigo presente en la sala (Costo: **100** unidades de tiempo). Si hay varios enemigos, la consola desplegará una lista enumerada para que selecciones el objetivo numérico específico.

### Gestión de Puertas
* **`abrir`**: Permite abrir una salida bloqueada o cerrada de la sala. El sistema te pedirá ingresar la dirección y validará de forma automática si posees la llave requerida en tu inventario (Costo: **50** unidades de tiempo).
- **`cerrar`**: Permite cerrar una puerta de la sala en una dirección específica (Costo: **50** unidades de tiempo).

### Gestión y Uso de Inventario
* **`recoger`**: Despliega un menú interactivo con los objetos disponibles en el suelo de la sala para que elijas cuál guardar en tu inventario (Costo: **25** unidades de tiempo).
- **`siguiente`** (o **`sig`**): Desplaza el puntero circular de tu inventario hacia el próximo objeto.
* **`anterior`** (o **`ant`**): Retrocede el puntero circular de tu inventario hacia el objeto anterior.
* **`usar`**: Aplica o consume el efecto del objeto que se encuentra actualmente seleccionado en tu inventario (Costo: **50** unidades de tiempo).
- **`soltar`**: Deja caer el objeto seleccionado actualmente al suelo de la sala actual (Costo: **25** unidades de tiempo).

### Control de Partida
* **`salir`**: Cierra la sesión de juego. El sistema te ofrecerá la opción de guardar tu progreso actual en un archivo antes de salir definitivamente.

## 4. Reglas del Reloj Virtual y Supervivencia
* **Tiempos y Turnos Asíncronos:** Cada acción que realizas consume una cantidad específica de tiempo en el reloj virtual del juego. Debido a esto, los enemigos y las trampas reaccionarán de manera dinámica en función del tiempo acumulado.
* **Condición de Victoria:** El juego concluye con éxito al alcanzar la sala de salida designada de la cripta.
* **Condición de Derrota:** Si tu vida llega a `0` o menos, tu personaje morirá. En ese instante se activará el registro de puntaje en la tabla general, se guardará el log cronológico de la partida en la carpeta `logs/` y se imprimirá un resumen detallado con las estadísticas finales de tu desempeño.
```
