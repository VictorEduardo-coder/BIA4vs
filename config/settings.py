import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "bia4vs_history.db"

FREE_AI_URL = "https://text.pollinations.ai/openai"
LOCAL_AI_URL = os.getenv("BIA4VS_LOCAL_URL", "http://localhost:11434/v1/chat/completions")
AI_MODEL = os.getenv("BIA4VS_MODEL", "openai")

MAX_CONTEXT_MESSAGES = 12
MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".java", ".py", ".js", ".ts", ".html", ".css",
    ".cpp", ".c", ".sql", ".json", ".xml", ".md",
    ".txt", ".pdf"
}

COLORS = {
    "bg_primary": "#071426",
    "bg_secondary": "#0B1D35",
    "panel": "#102744",
    "input_bg": "#0A1930",
    "blue_primary": "#247BFF",
    "blue_secondary": "#1765D1",
    "cyan": "#00CFFF",
    "text_primary": "#EAF3FF",
    "text_secondary": "#91A9C9",
    "success": "#00D68F",
    "warning": "#FFCC66",
    "error": "#FF526B"
}

SYSTEM_PROMPT = (
    "Você é a BIA4vs, uma assistente de inteligência artificial simplificada, "
    "profissional, direta e analítica, especializada em pesquisas técnicas, "
    "programação e análise de código. "
    "Regras obrigatórias: "
    "1. Priorize eficiência, clareza e precisão técnica. "
    "2. Não invente informações, links ou trechos de código. "
    "3. Diferencie erros confirmados de hipóteses ou suspeitas. "
    "4. Não afirme que executou códigos ou modificou ficheiros locais. "
    "5. Ao refatorar código, preserve as funcionalidades existentes e explique alterações relevantes. "
    "6. Quando utilizar resultados de pesquisa externa, cite a origem e apresente os links fornecidos."
)