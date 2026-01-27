import os
from typing import Optional
from .file_handlers.txt_handler import TxtHandler
from .file_handlers.pdf_handler import PdfHandler

class FileProcessor:
    def __init__(self):
        self._handlers = [
            TxtHandler(),
            PdfHandler(),
            # Future: JsonHandler(), etc.
        ]

    def __call__(self, file_path: str) -> str:
        handler = self.get_handler(file_path)
        with open(file_path, "rb") as f:
            return handler.read_content(f)
    
    def get_handler(self, filename: str):
        _, ext = os.path.splitext(filename)
        ext = ext.lstrip('.').lower()  # Remove leading dot and convert to lowercase
        
        for handler in self._handlers:
            if handler.can_handle(ext):
                return handler
        
        raise ValueError(f"Tipo de archivo no soportado: {ext}")
    
    def process_file(self, file, filename: str) -> str:
        handler = self.get_handler(filename)
        return handler.read_content(file)

# Instancia global para usar en toda la aplicación
file_processor = FileProcessor()
