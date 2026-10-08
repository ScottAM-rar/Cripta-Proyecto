import requests
import uuid
import time

""" Este es el adaptador que habla con el servicio HTTP de Cripta 
    
    Entonces el modelo y el motor de eventos no van a hacer requests, todo va a ser
    por metodos de esta clase para poder sustituirla por un cliente offline sin que nadie mas se entere del cambio
"""
class ClienteCripta:

    def __init__(self, base_url: str, timeout: int = 10) -> None:
        self.base_url = base_url.strip("/")
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())
        self.headers = {"X-Cripta-Client-Id": self.client_id}
        self.solicitudes_realizadas = 0

    def _solicitar(self, ruta: str) -> dict:

        url = f"{self.base_url}{ruta}"

        while True:
            respuesta = requests.get(url, headers=self.headers, timeout=self.timeout)
            self.solicitudes_realizadas += 1

            if respuesta.status_code == 200:
                return respuesta.json()
            
            if respuesta.status_code == 429:
                segundos_espera = respuesta.json()["reintentar_en"]
                time.sleep(segundos_espera)
                continue

            raise RuntimeError(f"Error al pedir {url}: {respuesta.status_code}")

    def obtener_criptas(self) -> list[dict]:
        return self._solicitar("/criptas")["criptas"]

    def obtener_datos_generales(self, cripta_id: str) -> dict:
        return self._solicitar(f"/criptas/{cripta_id}")

    def obtener_salas(self, cripta_id: str) -> list[dict]:
        salas: list[dict] = []
        pagina = 1
        total_paginas = 1

        while pagina <= total_paginas:
            respuesta = self._solicitar(f"/criptas/{cripta_id}/salas?pagina={pagina}")
            salas.extend(respuesta["salas"])
            total_paginas = respuesta["total_paginas"]
            pagina += 1

        return salas

    def obtener_contenido(self, cripta_id: str, salas: list[int]) -> list[dict]:
        contenido: list[dict] = []

        for inicio in range(0, len(salas), 10):
            lote = salas[inicio:inicio + 10]
            ids_texto = ",".join(str(sala_id) for sala_id in lote)
            respuesta = self._solicitar(f"/criptas/{cripta_id}/contenido?salas={ids_texto}")
            contenido.extend(respuesta["contenido"])

        return contenido

    def obtener_catalogo(self, ids: list[str]) -> list[dict]:
        catalogo: list[dict] = []

        for inicio in range(0, len(ids), 10):
            lote = ids[inicio:inicio + 10]
            ids_texto = ",".join(lote)
            respuesta = self._solicitar(f"/catalogo?ids={ids_texto}")
            catalogo.extend(respuesta["entidades"])

        return catalogo

    def obtener_version_cripta(self, cripta_id: str) -> str:
        return self._solicitar(f"/criptas/{cripta_id}/version")["version"]

    def obtener_version_catalogo(self) -> str:
        return self._solicitar("/catalogo/version")["version"]