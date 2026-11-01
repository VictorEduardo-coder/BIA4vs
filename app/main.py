import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QMessageBox
)
from app.interface.styles import MAIN_STYLESHEET
from app.interface.header import HeaderWidget
from app.interface.sidebar import SidebarWidget
from app.interface.chat import ChatAreaWidget
from app.storage.conversation_history import ConversationHistory
from app.files.attachment_manager import AttachmentManager
from app.code_analysis.analyzer import CodeAnalyzer
from app.research.search_engine import SearchEngine
from app.core.context_manager import ContextManager
from app.core.ai_engine import AIWorker


class BIA4vsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BIA4vs — Assistente de Pesquisa e Análise de Código")
        self.resize(1120, 740)
        self.setStyleSheet(MAIN_STYLESHEET)

        self.history = ConversationHistory()
        self.attachments = AttachmentManager()
        self.analyzer = CodeAnalyzer()
        self.search_engine = SearchEngine()
        self.context_manager = ContextManager(self.history, self.analyzer)
        self.current_conversation_id = None
        self.worker = None

        central = QWidget()
        self.setCentralWidget(central)
        root_layout = QHBoxLayout(central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self.sidebar = SidebarWidget()
        self.header = HeaderWidget()
        self.chat_area = ChatAreaWidget()

        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.setSpacing(0)
        right_panel.addWidget(self.header)
        right_panel.addWidget(self.chat_area, 1)

        root_layout.addWidget(self.sidebar)
        root_layout.addLayout(right_panel, 1)

        self._connect_signals()
        self._load_initial_conversation()

    def _connect_signals(self):
        self.sidebar.new_conversation_requested.connect(self.create_new_conversation)
        self.sidebar.conversation_selected.connect(self.switch_conversation)
        self.sidebar.rename_conversation_requested.connect(self.rename_conversation)
        self.sidebar.delete_conversation_requested.connect(self.delete_conversation)

        self.chat_area.send_requested.connect(self.handle_user_message)
        self.chat_area.file_attached.connect(self.handle_file_attached)
        self.chat_area.clear_attachments_requested.connect(self.clear_attachments)

    def _load_initial_conversation(self):
        conversations = self.history.list_conversations()
        if not conversations:
            self.create_new_conversation()
        else:
            self.switch_conversation(conversations[0]["id"])

    def _refresh_sidebar(self):
        conversations = self.history.list_conversations()
        self.sidebar.update_conversations(conversations, self.current_conversation_id)

    def create_new_conversation(self):
        self.current_conversation_id = self.history.create_conversation("Nova Conversa")
        self.chat_area.clear_messages()
        self.clear_attachments()
        self._refresh_sidebar()

    def switch_conversation(self, conversation_id):
        self.current_conversation_id = conversation_id
        self.chat_area.clear_messages()
        messages = self.history.get_messages(conversation_id)
        for msg in messages:
            self.chat_area.add_message_bubble(msg["role"], msg["content"])
        self._refresh_sidebar()

    def rename_conversation(self, conversation_id, new_title):
        self.history.rename_conversation(conversation_id, new_title)
        self._refresh_sidebar()

    def delete_conversation(self, conversation_id):
        self.history.delete_conversation(conversation_id)
        conversations = self.history.list_conversations()
        if conversations:
            self.switch_conversation(conversations[0]["id"])
        else:
            self.create_new_conversation()

    def handle_file_attached(self, file_path):
        try:
            self.attachments.add_file(file_path)
            self.chat_area.update_attachment_indicator(self.attachments.get_attachments())
        except Exception as exc:
            QMessageBox.warning(self, "Erro ao anexar ficheiro", str(exc))

    def clear_attachments(self):
        self.attachments.clear()
        self.chat_area.update_attachment_indicator([])

    def handle_user_message(self, text):
        if self.worker and self.worker.isRunning():
            return

        current_attachments = self.attachments.get_attachments()
        display_text = text
        if current_attachments:
            attached_names = ", ".join(a["name"] for a in current_attachments)
            display_text = f"**[Anexos: {attached_names}]**\n\n{text}"

        existing = self.history.get_messages(self.current_conversation_id, limit=1)
        if not existing:
            short_title = text[:32] + ("..." if len(text) > 32 else "")
            self.history.rename_conversation(self.current_conversation_id, short_title)
            self._refresh_sidebar()

        self.history.add_message(self.current_conversation_id, "user", display_text)
        self.chat_area.add_message_bubble("user", display_text)

        self.worker = AIWorker(
            self.current_conversation_id,
            text,
            current_attachments,
            self.context_manager,
            self.search_engine
        )
        self.worker.status_changed.connect(self.header.set_status)
        self.worker.response_ready.connect(self._on_ai_response)
        self.worker.error_occurred.connect(self._on_ai_error)
        self.clear_attachments()
        self.worker.start()

    def _on_ai_response(self, reply):
        self.history.add_message(self.current_conversation_id, "assistant", reply)
        self.chat_area.add_message_bubble("assistant", reply)

    def _on_ai_error(self, error_msg):
        formatted = f"**Erro de Processamento:** {error_msg}"
        self.chat_area.add_message_bubble("assistant", formatted)


def main():
    app = QApplication(sys.argv)
    window = BIA4vsWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()