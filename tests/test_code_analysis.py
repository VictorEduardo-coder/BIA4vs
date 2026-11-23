import unittest
from app.code_analysis.analyzer import CodeAnalyzer


class TestCodeAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = CodeAnalyzer()

    def test_valid_python_extracts_classes_functions_and_imports(self):
        attachment = {
            "name": "service.py",
            "extension": ".py",
            "content": (
                "import os\n"
                "from pathlib import Path\n\n"
                "class RepoService:\n"
                "    def load(self):\n"
                "        return Path(os.getcwd())\n"
            ),
        }
        diag = self.analyzer.analyze_attachment(attachment)
        self.assertIn("Linguagem/Tipo: Python", diag)
        self.assertIn("Sintaxe Python: Válida", diag)
        self.assertIn("RepoService", diag)
        self.assertIn("load", diag)
        self.assertIn("os", diag)
        self.assertIn("pathlib", diag)

    def test_invalid_python_reports_syntax_error_line(self):
        attachment = {
            "name": "broken.py",
            "extension": ".py",
            "content": "def broken(:\n    pass\n",
        }
        diag = self.analyzer.analyze_attachment(attachment)
        self.assertIn("Erro de Sintaxe Confirmado na linha 1", diag)

    def test_java_detects_unbalanced_braces_and_imports(self):
        attachment = {
            "name": "App.java",
            "extension": ".java",
            "content": (
                "import java.util.List;\n"
                "public class App {\n"
                "    void run() {\n"
                "}\n"
            ),
        }
        diag = self.analyzer.analyze_attachment(attachment)
        self.assertIn("Linguagem/Tipo: Java", diag)
        self.assertIn("Desequilíbrio de chavetas", diag)
        self.assertIn("java.util.List", diag)

    def test_sql_flags_unsafe_delete_and_update_without_where(self):
        unsafe_sql = {
            "name": "migration.sql",
            "extension": ".sql",
            "content": "DELETE FROM usuarios;\nUPDATE fichas SET gold = 0;\n",
        }
        diag = self.analyzer.analyze_attachment(unsafe_sql)
        self.assertIn("DELETE sem cláusula WHERE", diag)
        self.assertIn("UPDATE sem cláusula WHERE", diag)

    def test_sql_with_where_clause_has_no_critical_alert(self):
        safe_sql = {
            "name": "safe.sql",
            "extension": ".sql",
            "content": "DELETE FROM usuarios WHERE id = 10;\nUPDATE fichas SET gold = 50 WHERE id = 2;\n",
        }
        diag = self.analyzer.analyze_attachment(safe_sql)
        self.assertNotIn("Alerta crítico", diag)


if __name__ == "__main__":
    unittest.main()
