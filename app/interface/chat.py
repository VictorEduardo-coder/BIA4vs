import markdown
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea, QFrame,
    QLabel, QTextEdit, QPushButton, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import Qt, pyqtSignal
from config.settings import COLORS, ALLOWED_EXTENSIONS


class PromptTextEdit(QTextEdit):
    submit_pressed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setObjectName("PromptInput")
        self.setPlaceholderText("Pergunte, pesquise ou envie um código para análise...")
        self.setFixedHeight(68)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and (
            event.modifiers() & Qt.ControlModifier
        ):
            self.submit_pressed.emit()
            return
        super().keyPressEvent(event)


class MessageBubble(QFrame):
    def __init__(self, role, content):
        super().__init__()
        is_user = role == "user"
        bg_color = COLORS["blue_secondary"] if is_user else COLORS["panel"]
        border_color = COLORS["blue_primary"] if is_user else COLORS["bg_secondary"]
        author = "Você" if is_user else "BIA4vs"
        author_color = COLORS["text_primary"] if is_user else COLORS["cyan"]

        self.setStyleSheet(
            f"""
            QFrame {{
                background-color: {bg_color};
                border: 1px solid {border_color};
                border-radius: 10px;
                padding: 10px 14px;
            }}
            """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(6)

        header = QLabel(author)
        header.setStyleSheet(f"font-weight: 700; font-size: 12px; color: {author_color}; border: none;")

        html_body = markdown.markdown(
            content,
            extensions=["fenced_code", "tables", "codehilite"]
        )
        styled_html = (
            f"<style>"
            f"pre, code {{ background-color: {COLORS['input_bg']}; color: {COLORS['text_primary']}; "
            f"font-family: 'JetBrains Mono', 'Fira Code', monospace; padding: 6px; border-radius: 6px; }}"
            f"a {{ color: {COLORS['cyan']}; }}"
            f"</style>{html_body}"
        )

        body = QLabel(styled_html)
        body.setWordWrap(True)
        body.setTextFormat(Qt.RichText)
        body.setTextInteractionFlags(Qt.TextSelectableByMouse | Qt.LinksAccessibleByMouse)
        body.setOpenExternalLinks(True)
        body.setStyleSheet(f"color: {COLORS['text_primary']}; border: none;")

        layout.addWidget(header)
        layout.addWidget(body)


class ChatAreaWidget(QWidget):
    send_requested = pyqtSignal(str)
    file_attached = pyqtSignal(str)
    clear_attachments_requested = pyqtSignal()

    def __init__(self):
        super().__init__()
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setContentsMargins(24, 20, 24, 20)
        self.messages_layout.setSpacing(14)
        self.messages_layout.addStretch()

        self.scroll_area.setWidget(self.messages_container)

        self.footer = QFrame()
        self.footer.setObjectName("FooterFrame")
        footer_layout = QVBoxLayout(self.footer)
        footer_layout.setContentsMargins(20, 10, 20, 14)
        footer_layout.setSpacing(6)

        self.attachments_bar = QHBoxLayout()
        self.attachments_label = QLabel("")
        self.attachments_label.setStyleSheet(f"color: {COLORS['cyan']}; font-size: 12px;")
        self.clear_att_btn = QPushButton("Limpar anexos")
        self.clear_att_btn.setVisible(False)
        self.clear_att_btn.clicked.connect(self.clear_attachments_requested.emit)

        self.attachments_bar.addWidget(self.attachments_label)
        self.attachments_bar.addStretch()
        self.attachments_bar.addWidget(self.clear_att_btn)

        input_row = QHBoxLayout()
        input_row.setSpacing(10)

        self.attach_btn = QPushButton("Anexar")
        self.attach_btn.setFixedHeight(42)
        self.attach_btn.clicked.connect(self._open_file_dialog)

        self.prompt_input = PromptTextEdit()
        self.prompt_input.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.prompt_input.submit_pressed.connect(self._trigger_send)

        self.send_btn = QPushButton("Enviar")
        self.send_btn.setObjectName("PrimaryButton")
        self.send_btn.setFixedHeight(42)
        self.send_btn.clicked.connect(self._trigger_send)

        input_row.addWidget(self.attach_btn)
        input_row.addWidget(self.prompt_input, 1)
        input_row.addWidget(self.send_btn)

        footer_layout.addLayout(self.attachments_bar)
        footer_layout.addLayout(input_row)

        main_layout.addWidget(self.scroll_area, 1)
        main_layout.addWidget(self.footer)

    def add_message_bubble(self, role, content):
        bubble = MessageBubble(role, content)
        count = self.messages_layout.count()
        self.messages_layout.insertWidget(count - 1, bubble)
        self.scroll_area.verticalScrollBar().setValue(
            self.scroll_area.verticalScrollBar().maximum()
        )

    def clear_messages(self):
        while self.messages_layout.count() > 1:
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def update_attachment_indicator(self, attachments):
        if not attachments:
            self.attachments_label.setText("")
            self.clear_att_btn.setVisible(False)
            return
        names = ", ".join(item["name"] for item in attachments)
        self.attachments_label.setText(f"Anexos ({len(attachments)}): {names}")
        self.clear_att_btn.setVisible(True)

    def _open_file_dialog(self):
        exts = " ".join(f"*{ext}" for ext in sorted(ALLOWED_EXTENSIONS))
        files, _ = QFileDialog.getOpenFileNames(
            self, "Selecionar ficheiros para análise", "", f"Ficheiros suportados ({exts})"
        )
        for path in files:
            self.file_attached.emit(path)

    def _trigger_send(self):
        text = self.prompt_input.toPlainText().strip()
        if not text:
            return
        self.prompt_input.clear()
        self.send_requested.emit(text)