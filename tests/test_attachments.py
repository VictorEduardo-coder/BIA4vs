import tempfile
import unittest
from pathlib import Path
from app.files.attachment_manager import AttachmentManager
from config.settings import MAX_FILE_SIZE_BYTES


class TestAttachmentManager(unittest.TestCase):
    def setUp(self):
        self.manager = AttachmentManager()
        self.tmp = tempfile.TemporaryDirectory()
        self.tmp_dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_add_valid_source_file_and_clear(self):
        sample = self.tmp_dir / "consulta.sql"
        sample.write_text("SELECT id, nome FROM fichas WHERE nivel >= 5;", encoding="utf-8")

        item = self.manager.add_file(sample)
        self.assertEqual(item["name"], "consulta.sql")
        self.assertEqual(item["extension"], ".sql")
        self.assertIn("SELECT id, nome", item["content"])
        self.assertEqual(len(self.manager.get_attachments()), 1)

        # Defensive copy check
        returned = self.manager.get_attachments()
        returned.clear()
        self.assertEqual(len(self.manager.get_attachments()), 1)

        self.manager.clear()
        self.assertEqual(len(self.manager.get_attachments()), 0)

    def test_rejects_missing_file(self):
        with self.assertRaises(ValueError) as ctx:
            self.manager.add_file(self.tmp_dir / "inexistente.py")
        self.assertIn("não encontrado", str(ctx.exception))

    def test_rejects_unsupported_extension(self):
        disallowed = self.tmp_dir / "script.exe"
        disallowed.write_bytes(b"binary")
        with self.assertRaises(ValueError) as ctx:
            self.manager.add_file(disallowed)
        self.assertIn("Formato não suportado", str(ctx.exception))

    def test_rejects_file_larger_than_2mb(self):
        oversized = self.tmp_dir / "grande.txt"
        oversized.write_bytes(b"a" * (MAX_FILE_SIZE_BYTES + 1))
        with self.assertRaises(ValueError) as ctx:
            self.manager.add_file(oversized)
        self.assertIn("excede o limite de 2 MB", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
