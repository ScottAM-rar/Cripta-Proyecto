import requests
import uuid
import time

""" Este es el adaptador que habla con el servicio HTTP de Cripta 
    
    Entonces el modelo y el motor de eventos no van a hacer requests, todo va a ser
    por metodos de esta clase para poder sustituirla por un cliente offline sin que nadie mas se entere del cambio
"""
class ClienteCripta:

    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.strip("/")
        self.timeout = timeout
        self.client_id = str(uuid.uuid4())
        self.headers = {"X-Cripta-Client-Id": self.client_id}
        self.solicitudes_realizadas = 0

    