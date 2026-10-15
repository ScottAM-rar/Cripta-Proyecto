from __future__ import annotations

import json

from adaptadores.extension import ruta_archivo, EXTENSION_LOG, CARPETA_LOGS


class RegistroEvento:
    """Datos de un evento cargado desde un archivo de repetición."""

    def __init__(
        self,
        tipo_accion: str,
        tiempo_ejecucion: int,
        actor,
        datos_extra: list,
    ):
        self.tipo_accion = tipo_accion
        self.tiempo_ejecucion = tiempo_ejecucion
        self.actor = actor
        self.datos_extra = datos_extra


class ReferenciaEvento:
    """Referencia simple a un objeto guardado en el archivo de replay."""

    def __init__(self, tipo: str, identificador=None, sala=None):
        self.tipo = tipo
        self.id = identificador
        self.sala = sala


class NodoEvento:
    """Nodo de la lista enlazada de acciones del jugador."""

    def __init__(self, accion: str):
        self.accion = accion
        self.anterior: NodoEvento | None = None
        self.siguiente: NodoEvento | None = None


class LogEventos:
    """Lista doblemente enlazada con las acciones realizadas por el jugador."""

    def __init__(self, semilla: int = 0, id_cripta: str | None = None):
        self.cabeza: NodoEvento | None = None
        self.cola: NodoEvento | None = None
        self.cantidad = 0
        if not isinstance(semilla, int):
            raise TypeError("La semilla debe ser un entero")
        if id_cripta is not None and (
            not isinstance(id_cripta, str) or not id_cripta.strip()
        ):
            raise ValueError("El ID de la cripta debe ser texto no vacío")
        self.semilla = semilla
        self.id_cripta = id_cripta
        self._cursor_cronologico: NodoEvento | None = None

    def registrar_accion(
        self,
        tipo_accion: str,
        id_afectado: str | int | None = None,
    ) -> None:
        if not isinstance(tipo_accion, str) or not tipo_accion.strip():
            raise ValueError("El tipo de acción debe ser una cadena no vacía")

        if id_afectado is None:
            id_texto = "ninguno"
        elif isinstance(id_afectado, (str, int)):
            id_texto = str(id_afectado)
        else:
            raise TypeError("El ID afectado debe ser texto, entero o None")

        self.agregar(json.dumps({
            "tipo_accion": tipo_accion.strip(),
            "id_afectado": id_texto,
            "tiempo_ejecucion": 100,
            "datos_extra": [],
        }, ensure_ascii=False))

    def registrar_evento(self, evento) -> None:
        """Guarda toda la información necesaria para reconstruir un evento."""
        registro = {
            "tipo_accion": evento.tipo_accion,
            "tiempo_ejecucion": evento.tiempo_ejecucion,
            "actor": self._serializar_valor(evento.actor),
            "datos_extra": [
                self._serializar_valor(dato) for dato in evento.datos_extra
            ],
        }
        self.agregar(json.dumps(registro, ensure_ascii=False))

    @staticmethod
    def _serializar_valor(valor):
        if valor is None or isinstance(valor, (str, int, float, bool)):
            return valor
        if isinstance(valor, list):
            return [LogEventos._serializar_valor(elemento) for elemento in valor]
        if isinstance(valor, tuple):
            return {
                "tipo": "tupla",
                "valores": [
                    LogEventos._serializar_valor(elemento) for elemento in valor
                ],
            }

        if type(valor).__name__ == "JugadorDTO":
            return {"tipo": "jugador"}

        if hasattr(valor, "id_instancia") and hasattr(valor, "id_sala"):
            return {
                "tipo": "trampa",
                "id": valor.id_instancia,
                "sala": valor.id_sala,
            }

        atributos = (
            ("id_instancia", "enemigo"),
            ("id_catalogo", "objeto"),
            ("id", "sala"),
        )
        for nombre, tipo in atributos:
            identificador = getattr(valor, nombre, None)
            if identificador is not None:
                registro = {"tipo": tipo, "id": identificador}
                return registro

        if hasattr(valor, "direccion"):
            return {"tipo": "salida", "direccion": valor.direccion}

        raise TypeError(
            f"No se puede guardar en el log el valor {type(valor).__name__}"
        )

    def obtener_registros_cronologicos(self) -> list[RegistroEvento]:
        """Devuelve los eventos completos en el orden en que ocurrieron."""
        registros: list[RegistroEvento] = []
        actual = self.cabeza
        while actual is not None:
            try:
                datos = json.loads(actual.accion)
            except json.JSONDecodeError as error:
                raise ValueError("El log contiene una acción con formato inválido") from error
            if not isinstance(datos, dict):
                raise ValueError("El registro del log debe ser un objeto JSON")
            registros.append(
                RegistroEvento(
                    datos.get("tipo_accion"),
                    datos.get("tiempo_ejecucion"),
                    self._deserializar_valor(datos.get("actor")),
                    [
                        self._deserializar_valor(valor)
                        for valor in datos.get("datos_extra", [])
                    ],
                )
            )
            actual = actual.siguiente
        return registros

    @staticmethod
    def _deserializar_valor(valor):
        if isinstance(valor, list):
            return [
                LogEventos._deserializar_valor(elemento)
                for elemento in valor
            ]
        if isinstance(valor, dict):
            if valor.get("tipo") == "tupla":
                return [
                    LogEventos._deserializar_valor(elemento)
                    for elemento in valor.get("valores", [])
                ]
            return ReferenciaEvento(
                valor.get("tipo"),
                valor.get("id"),
                valor.get("sala"),
            )
        return valor

    def agregar(self, accion: str) -> None:
        if not isinstance(accion, str) or not accion.strip():
            raise ValueError("La acción debe ser una cadena no vacía")

        nuevo = NodoEvento(accion.strip())
        if self.cola is None:
            self.cabeza = nuevo
            self.cola = nuevo
        else:
            nuevo.anterior = self.cola
            self.cola.siguiente = nuevo
            self.cola = nuevo
        self.cantidad += 1
        if self._cursor_cronologico is None:
            self._cursor_cronologico = nuevo

    def obtener_accion(self) -> str | None:
        """Extrae la última acción registrada, siguiendo un comportamiento LIFO."""
        if self.cola is None:
            return None

        nodo = self.cola
        self.cola = nodo.anterior
        if self.cola is None:
            self.cabeza = None
        else:
            self.cola.siguiente = None
        self.cantidad -= 1
        return nodo.accion

    def obtener_acciones(self) -> list[str]:
        """Devuelve las acciones desde la última registrada hasta la primera."""
        acciones: list[str] = []
        actual = self.cola
        while actual is not None:
            acciones.append(actual.accion)
            actual = actual.anterior
        return acciones

    def iniciar_recorrido_cronologico(self) -> None:
        """Prepara un recorrido desde la primera acción registrada."""
        self._cursor_cronologico = self.cabeza

    def siguiente_accion_cronologica(self) -> str | None:
        """Devuelve la siguiente acción sin eliminarla de la lista."""
        if self._cursor_cronologico is None:
            return None

        accion = self._cursor_cronologico.accion
        self._cursor_cronologico = self._cursor_cronologico.siguiente
        return accion

    def obtener_acciones_cronologicas(self) -> list[str]:
        """Devuelve las acciones desde la primera registrada hasta la última."""
        acciones: list[str] = []
        actual = self.cabeza
        while actual is not None:
            acciones.append(actual.accion)
            actual = actual.siguiente
        return acciones

    def como_string(self, separador: str = ", ") -> str:
        acciones = self.obtener_acciones()
        return separador.join(acciones)

    def guardar_log(self, nombre_archivo: str) -> None:
        """Guarda las acciones en un archivo .log, una acción por línea."""
        nombre_archivo = ruta_archivo(nombre_archivo, EXTENSION_LOG, CARPETA_LOGS, crear_carpeta=True)

        with open(nombre_archivo, "w", encoding="utf-8") as archivo:
            archivo.write(f"cripta: {self.id_cripta or 'ninguna'}\n")
            archivo.write(f"semilla: {self.semilla}\n")
            actual = self.cabeza
            while actual is not None:
                archivo.write(actual.accion + "\n")
                actual = actual.siguiente

    def cargar_log(self, nombre_archivo: str) -> None:
        """Carga las acciones de un archivo .log y reemplaza las actuales."""
        nombre_archivo = ruta_archivo(nombre_archivo, EXTENSION_LOG, CARPETA_LOGS)

        with open(nombre_archivo, "r", encoding="utf-8") as archivo:
            lineas = [linea.rstrip("\n") for linea in archivo]

        if len(lineas) < 2 or not lineas[0].startswith("cripta: "):
            raise ValueError("El archivo .log no contiene una cripta válida")
        id_cripta = lineas[0][len("cripta: "):]
        if id_cripta == "ninguna":
            id_cripta = None
        elif not id_cripta.strip():
            raise ValueError("El ID de la cripta del archivo .log no es válido")
        if not lineas[1].startswith("semilla: "):
            raise ValueError("El archivo .log no contiene una semilla válida")
        try:
            semilla = int(lineas[1][len("semilla: "):])
        except ValueError as error:
            raise ValueError("La semilla del archivo .log debe ser un entero") from error

        self.vaciar()
        self.id_cripta = id_cripta
        self.semilla = semilla
        for accion in lineas[2:]:
            if accion.strip():
                self.agregar(accion)

    def vaciar(self) -> None:
        self.cabeza = None
        self.cola = None
        self.cantidad = 0
        self._cursor_cronologico = None