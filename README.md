
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
   Mediciones: python main.py --bench
   Mediciones de terreno y cazador: python main.py --bench terreno
   Pruebas: python -m unittest discover -p "test_*.py"
   Datos generados: datos_cripta/, logs/, Partidas Guardadas/

## Desarrollo guiado por especificaciones (Parte II)

Capacidades (cada una en `specs/<NNN-nombre>/`): `001-terreno-y-cazador` (costo de las salidas y enemigo cazador). Las decisiones y su comparación con el plan original están en `DECISIONES.md`; los comandos de Spec Kit con texto propio, en `PROMPTS_LLM.md`.

**Compatibilidad de partidas guardadas**: el formato binario subió de la versión 5 a la 6 (costo por salida y rango por enemigo). Un archivo de una versión anterior se rechaza con un mensaje que indica la versión encontrada y la esperada; no se migra.

Para la Parte II se usa **GitHub Spec Kit** con el agente **Claude Code**.

| Herramienta | Versión |
|---|---|
| Spec Kit (`specify-cli`) | **1.2.3** |
| Agente | Claude Code |
| Python | 3.11+ |

Instalación (todo el equipo debe usar exactamente esta versión):

```bash
  # debe mostrar 1.2.3
```

Al clonar el repositorio no hace falta ejecutar `specify init`: la carpeta `.specify/` y los comandos `/speckit.*` ya están versionados.
