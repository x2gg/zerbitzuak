from .base_handler import FileHandler

class TxtHandler(FileHandler):
    @staticmethod
    def can_handle(extension: str) -> bool:
        return extension.lower() == 'txt'
    
    def read_content(self, file) -> str:
        if hasattr(file, 'read'):
            # Si es un objeto de archivo de Django
            return file.read().decode('utf-8')
        else:
            # Si es un objeto de archivo estándar
            return file.read()
