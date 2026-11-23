import re
import requests
from config.settings import FREE_AI_URL, LOCAL_AI_URL, AI_MODEL, LOCAL_ONLY, REQUEST_TIMEOUT_SECONDS


SENSITIVE_PATTERNS = [
    ("Chave privada PEM", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    ("Token/Chave AWS", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("Chave API OpenAI/GitHub", re.compile(r"\b(?:sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{20,})\b")),
    ("Credencial hardcoded", re.compile(r"(?i)\b(?:password|passwd|senha|api_key|secret_key|db_password)\s*[:=]\s*['\"]?[^\s'\"]{4,}")),
    ("Header Bearer Token", re.compile(r"(?i)Authorization\s*:\s*Bearer\s+[A-Za-z0-9._-]{12,}")),
]


def scan_sensitive_content(text):
    """Detecta padrões comuns de segredos antes de enviar dados para provedores remotos."""
    if not text:
        return []
    findings = []
    for label, pattern in SENSITIVE_PATTERNS:
        if pattern.search(text):
            findings.append(label)
    return findings


class AIEngineClient:
    """Cliente HTTP desacoplado da UI (PyQt5) para facilitar testes, fallback e privacidade."""

    def __init__(
        self,
        remote_url=FREE_AI_URL,
        local_url=LOCAL_AI_URL,
        model=AI_MODEL,
        local_only=LOCAL_ONLY,
        timeout=REQUEST_TIMEOUT_SECONDS,
        http_post=None,
    ):
        self.remote_url = remote_url
        self.local_url = local_url
        self.model = model
        self.local_only = local_only
        self.timeout = timeout
        self.http_post = http_post or requests.post

    def describe_privacy_mode(self):
        if self.local_only:
            return f"Modo somente local ativo (Ollama em {self.local_url}; nenhum dado enviado a terceiros)."
        return f"Modo híbrido (provedor externo {self.remote_url} com fallback local {self.local_url})."

    def candidate_endpoints(self, has_sensitive_data=False):
        if self.local_only or has_sensitive_data:
            return [self.local_url]
        return [self.remote_url, self.local_url]

    def request_completion(self, messages, has_sensitive_data=False, cancelled_fn=None):
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
        }

        last_errors = []
        for url in self.candidate_endpoints(has_sensitive_data=has_sensitive_data):
            if cancelled_fn and cancelled_fn():
                return None, ["Operação cancelada pelo usuário."]
            try:
                response = self.http_post(url, headers=headers, json=payload, timeout=self.timeout)
                if response.status_code == 429:
                    last_errors.append(f"Limite de requisições (HTTP 429) em {url}")
                    continue
                if response.status_code != 200:
                    last_errors.append(f"Resposta HTTP {response.status_code} em {url}")
                    continue

                data = response.json()
                if not isinstance(data, dict):
                    last_errors.append(f"JSON inesperado em {url}")
                    continue

                choices = data.get("choices")
                if not isinstance(choices, list) or not choices:
                    last_errors.append(f"Resposta vazia do modelo em {url}")
                    continue

                message = choices[0].get("message") if isinstance(choices[0], dict) else None
                content = message.get("content") if isinstance(message, dict) else None
                if isinstance(content, str) and content.strip():
                    return content.strip(), last_errors
                last_errors.append(f"Conteúdo vazio retornado por {url}")
            except requests.Timeout:
                last_errors.append(f"Timeout após {self.timeout}s em {url}")
            except requests.ConnectionError:
                last_errors.append(f"Falha de conexão/DNS em {url}")
            except ValueError:
                last_errors.append(f"JSON malformado retornado por {url}")
            except Exception as exc:
                last_errors.append(f"Erro inesperado em {url}: {exc}")

        return None, last_errors

    def build_offline_diagnostics(self, attachments, code_analyzer, search_context=None, warnings=None):
        parts = ["**Diagnóstico Local Offline — BIA4vs**"]
        if warnings:
            parts.append("### Avisos de Privacidade / Conectividade\n" + "\n".join(f"- {w}" for w in warnings))
        if search_context:
            parts.append(f"### Resultados de Pesquisa\n```text\n{search_context}\n```")
        if attachments:
            parts.append("### Análise Estática Preliminar de Ficheiros")
            for item in attachments:
                diag = code_analyzer.analyze_attachment(item)
                parts.append(f"**{item['name']}**\n```text\n{diag}\n```")
        if not search_context and not attachments:
            parts.append(
                "Sem ligação ao motor de IA no momento. "
                "Anexe um ficheiro de código para executar análise estática offline ou inicie o Ollama local."
            )
        return "\n\n".join(parts)
