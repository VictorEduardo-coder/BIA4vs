import ast
import re


class CodeAnalyzer:
    LANGUAGE_MAP = {
        ".java": "Java",
        ".py": "Python",
        ".js": "JavaScript",
        ".ts": "TypeScript",
        ".html": "HTML",
        ".css": "CSS",
        ".cpp": "C++",
        ".c": "C",
        ".sql": "SQL",
        ".json": "JSON",
        ".xml": "XML",
        ".md": "Markdown",
        ".txt": "Texto",
        ".pdf": "PDF"
    }

    def analyze_attachment(self, attachment):
        ext = attachment["extension"]
        content = attachment["content"]
        lang = self.LANGUAGE_MAP.get(ext, "Desconhecida")
        lines = content.splitlines()

        diagnostics = [
            f"Ficheiro: {attachment['name']} | Linguagem/Tipo: {lang} | Linhas: {len(lines)}"
        ]

        if ext == ".py":
            diagnostics.extend(self._analyze_python(content))
        elif ext in {".java", ".c", ".cpp", ".js", ".ts"}:
            diagnostics.extend(self._analyze_c_family(content))
        elif ext == ".sql":
            diagnostics.extend(self._analyze_sql(content))

        return "\n".join(diagnostics)

    def _analyze_python(self, content):
        notes = []
        try:
            tree = ast.parse(content)
            funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
            classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
            notes.append(f"Sintaxe Python: Válida (AST verificada).")
            if classes:
                notes.append(f"Classes identificadas: {', '.join(classes)}")
            if funcs:
                notes.append(f"Funções identificadas: {', '.join(funcs)}")
            if imports:
                notes.append(f"Dependências/Imports: {', '.join(sorted(set(imports)))}")
        except SyntaxError as err:
            notes.append(f"Erro de Sintaxe Confirmado na linha {err.lineno}: {err.msg}")
        return notes

    def _analyze_c_family(self, content):
        notes = []
        open_braces = content.count("{")
        close_braces = content.count("}")
        if open_braces != close_braces:
            notes.append(
                f"Alerta estrutural: Desequilíbrio de chavetas ({{: {open_braces}, }}: {close_braces})."
            )
        imports = re.findall(r"^(?:import|#include)\s+([^\r\n;]+)", content, re.MULTILINE)
        if imports:
            notes.append(f"Dependências detetadas: {', '.join(imports[:15])}")
        return notes

    def _analyze_sql(self, content):
        notes = []
        upper = content.upper()
        if "DELETE FROM" in upper and "WHERE" not in upper:
            notes.append("Alerta crítico: Instrução DELETE sem cláusula WHERE detetada.")
        if "UPDATE " in upper and "WHERE" not in upper:
            notes.append("Alerta crítico: Instrução UPDATE sem cláusula WHERE detetada.")
        return notes