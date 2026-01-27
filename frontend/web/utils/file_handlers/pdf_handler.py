from .base_handler import FileHandler
import io
from PyPDF2 import PdfReader

class PdfHandler(FileHandler):
    @staticmethod
    def can_handle(extension: str) -> bool:
        return extension.lower() == 'pdf'

    def read_content(self, file) -> str:
        # file can be a Django UploadedFile or a binary file-like
        # We need bytes for PdfReader
        if hasattr(file, 'read'):
            # In Django UploadedFile, read() returns bytes
            data = file.read()
            # Reset pointer if subsequent code might reuse it (defensive)
            try:
                file.seek(0)
            except Exception:
                pass
            bio = io.BytesIO(data)
            reader = PdfReader(bio)
        else:
            # Fallback: assume it is a file-like opened in binary mode
            data = file.read()
            bio = io.BytesIO(data)
            reader = PdfReader(bio)

        text_parts = []
        for page in reader.pages:
            try:
                page_text = page.extract_text() or ''
            except Exception:
                page_text = ''
            text_parts.append(page_text)
        return "\n".join(text_parts).strip()
