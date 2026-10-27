
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
   Datos generados: datos_cripta/, logs/, Partidas Guardadas/

## Desarrollo guiado por especificaciones (Parte II)

Para la Parte II se usa **GitHub Spec Kit** con el agente **Claude Code**.

| Herramienta | Versión |
|---|---|
| Spec Kit (`specify-cli`) | **1.2.3** |
| Agente | Claude Code |
| Python | 3.11+ |

Instalación (todo el equipo debe usar exactamente esta versión):

```bash
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v1.2.3
specify version   # debe mostrar 1.2.3
```

Al clonar el repositorio no hace falta ejecutar `specify init`: la carpeta `.specify/` y los comandos `/speckit.*` ya están versionados.
