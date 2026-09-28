from DTO.Objeto import Objeto

class ObjetoLogica:
    def __init__(self, objeto: Objeto):
        self.objeto = objeto
        
    def usar_objeto(self):
        """Logica para usar el objeto. Varia segun el tipo de objeto."""
        if self.objeto.tipo == "pocion":
            # Lógica para usar una poción
            pass
        elif self.objeto.tipo == "llave":
            # Lógica para usar una llave
            pass
        # Agregar más tipos de objetos según sea necesario