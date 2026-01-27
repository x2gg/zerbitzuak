from abc import ABC, abstractmethod

class FileHandler(ABC):
    @staticmethod
    @abstractmethod
    def can_handle(extension: str) -> bool:
        """Determina si este manejador puede procesar el tipo de archivo"""
        pass
    
    @abstractmethod
    def read_content(self, file) -> str:
        """Lee y devuelve el contenido del archivo como texto"""
        pass
