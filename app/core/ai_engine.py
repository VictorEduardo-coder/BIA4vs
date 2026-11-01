import requests
from PyQt5.QtCore import QThread, pyqtSignal
from config.settings import FREE_AI_URL, LOCAL_AI_URL, AI_MODEL


class AIWorker(QThread):
    response_ready = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, conversation_id, user_text, attachments, context_manager, search_engine):
        super().__init__()
        self.conversation_id = conversation_id
        self.user_text = user_text
        self.attachments = attachments
        self.context_manager = context_manager
        self.search_engine = search_engine

    def run(self):
        try:
            self.status_changed.emit("Processando")
            search_context = None

            if self.search_engine.needs_external_search(self.user_text):
                self.status_changed.emit("Conectando")
                results = self.search_engine.search(self.user_text)
                search_context = self.search_engine.format_results_for_context(results)
                self.status_changed.emit("Processando")

            messages = self.context_manager.build_messages(
                self.conversation_id,
                self.user_text,
                self.attachments,
                search_context
            )

            reply = self._request_keyless_ai(messages)
            if not reply:
                reply = self._local_offline_analysis(search_context)

            self.status_changed.emit("Online")
            self.response_ready.emit(reply)

        except Exception as exc:
            self.status_changed.emit("Desconectado")
            self.error_occurred.emit(str(exc))

    def _request_keyless_ai(self, messages):
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": AI_MODEL,
            "messages": messages,
            "temperature": 0.2
        }

        for url in (FREE_AI_URL, LOCAL_AI_URL):
            try:
                response = requests.post(url, headers=headers, json=payload, timeout=45)
                if response.status_code == 200:
                    data = response.json()
                    choices = data.get("choices", [])
                    if choices and "message" in choices[0]:
                        return choices[0]["message"]["content"]
            except Exception:
                continue
        return None

    def _local_offline_analysis(self, search_context):
        parts = ["**Diagnóstico Local Offline — BIA4vs**"]
        if search_context:
            parts.append(f"### Resultados de Pesquisa\n```text\n{search_context}\n```")
        if self.attachments:
            parts.append("### Análise Estática de Ficheiros")
            for item in self.attachments:
                diag = self.context_manager.code_analyzer.analyze_attachment(item)
                parts.append(f"**{item['name']}**\n```text\n{diag}\n```")
        if not search_context and not self.attachments:
            parts.append(
                "Sem ligação ao motor de IA externo no momento. "
                "Anexe um ficheiro de código para realizar a análise estática offline ou verifique a ligação à internet."
            )
        return "\n\n".join(parts)