import shutil
import subprocess
from pathlib import Path
from config.settings import ALLOWED_EXTENSIONS, MAX_FILE_SIZE_BYTES

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


class AttachmentManager:
    def __init__(self):
        self.attachments = []

    def add_file(self, file_path):
        path = Path(file_path)
        if not path.exists() or not path.is_file():
            raise ValueError(f"Ficheiro não encontrado: {path.name}")

        ext = path.suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise ValueError(f"Formato não suportado: {ext}")

        if path.stat().st_size > MAX_FILE_SIZE_BYTES:
            raise ValueError(f"O ficheiro {path.name} excede o limite de 2 MB.")

        content = self._read_file(path, ext)
        item = {
            "name": path.name,
            "path": str(path),
            "extension": ext,
            "content": content
        }
        self.attachments.append(item)
        return item

    def _read_file(self, path, ext):
        if ext == ".pdf":
            if PdfReader is not None:
                reader = PdfReader(str(path))
                pages = [page.extract_text() or "" for page in reader.pages]
                return "\n".join(pages).strip()
            if shutil.which("pdftotext"):
                result = subprocess.run(
                    ["pdftotext", str(path), "-"],
                    capture_output=True,
                    text=True,
                    check=False
                )
                return result.stdout.strip()
            raise ValueError("Instale 'pypdf' ou 'poppler-utils' para ler ficheiros PDF.")
        return path.read_text(encoding="utf-8", errors="replace")

    def get_attachments(self):
        return list(self.attachments)

    def clear(self):
        self.attachments.clear()