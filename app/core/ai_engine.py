from PyQt5.QtCore import QThread, pyqtSignal
from app.core.ai_client import AIEngineClient, scan_sensitive_content


class AIWorker(QThread):
    response_ready = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    error_occurred = pyqtSignal(str)

    def __init__(self, conversation_id, user_text, attachments, context_manager, search_engine, client=None):
        super().__init__()
        self.conversation_id = conversation_id
        self.user_text = user_text
        self.attachments = attachments or []
        self.context_manager = context_manager
        self.search_engine = search_engine
        self.client = client or AIEngineClient()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def _collect_sensitive_findings(self):
        findings = list(scan_sensitive_content(self.user_text))
        for item in self.attachments:
            for hit in scan_sensitive_content(item.get("content", "")):
                findings.append(f"{hit} em {item.get('name', 'anexo')}")
        return findings

    def run(self):
        try:
            self.status_changed.emit("Processando")
            search_context = None
            sensitive_hits = self._collect_sensitive_findings()
            has_sensitive = len(sensitive_hits) > 0

            if not self.client.local_only and not has_sensitive and self.search_engine.needs_external_search(self.user_text):
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

            reply, errors = self.client.request_completion(
                messages,
                has_sensitive_data=has_sensitive,
                cancelled_fn=lambda: self._cancelled,
            )

            if self._cancelled:
                self.status_changed.emit("Cancelado")
                return

            warnings = []
            if has_sensitive:
                warnings.append(
                    "Possíveis dados sensíveis detetados ("
                    + ", ".join(sensitive_hits)
                    + "): envio para provedor remoto bloqueado por privacidade."
                )

            if not reply:
                warnings.extend(errors)
                reply = self.client.build_offline_diagnostics(
                    self.attachments,
                    self.context_manager.code_analyzer,
                    search_context=search_context,
                    warnings=warnings,
                )
            elif warnings:
                reply = "> ⚠️ " + " ".join(warnings) + "\n\n" + reply

            self.status_changed.emit("Online")
            self.response_ready.emit(reply)

        except Exception as exc:
            self.status_changed.emit("Desconectado")
            self.error_occurred.emit(str(exc))
