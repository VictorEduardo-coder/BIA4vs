from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QHBoxLayout, QPushButton,
    QListWidget, QListWidgetItem, QInputDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal


class SidebarWidget(QFrame):
    conversation_selected = pyqtSignal(int)
    new_conversation_requested = pyqtSignal()
    rename_conversation_requested = pyqtSignal(int, str)
    delete_conversation_requested = pyqtSignal(int)

    def __init__(self):
        super().__init__()
        self.setObjectName("SidebarFrame")
        self.setFixedWidth(250)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        self.new_btn = QPushButton("+ Nova Conversa")
        self.new_btn.setObjectName("PrimaryButton")
        self.new_btn.clicked.connect(self.new_conversation_requested.emit)

        self.list_widget = QListWidget()
        self.list_widget.itemClicked.connect(self._on_item_clicked)

        actions_layout = QHBoxLayout()
        self.rename_btn = QPushButton("Renomear")
        self.rename_btn.clicked.connect(self._on_rename)

        self.delete_btn = QPushButton("Excluir")
        self.delete_btn.setObjectName("DangerButton")
        self.delete_btn.clicked.connect(self._on_delete)

        actions_layout.addWidget(self.rename_btn)
        actions_layout.addWidget(self.delete_btn)

        layout.addWidget(self.new_btn)
        layout.addWidget(self.list_widget, 1)
        layout.addLayout(actions_layout)

    def update_conversations(self, conversations, active_id=None):
        self.list_widget.clear()
        for conv in conversations:
            item = QListWidgetItem(conv["title"])
            item.setData(Qt.UserRole, conv["id"])
            self.list_widget.addItem(item)
            if conv["id"] == active_id:
                self.list_widget.setCurrentItem(item)

    def _on_item_clicked(self, item):
        conv_id = item.data(Qt.UserRole)
        self.conversation_selected.emit(conv_id)

    def _on_rename(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        conv_id = item.data(Qt.UserRole)
        new_title, ok = QInputDialog.getText(
            self, "Renomear Conversa", "Novo título:", text=item.text()
        )
        if ok and new_title.strip():
            self.rename_conversation_requested.emit(conv_id, new_title.strip())

    def _on_delete(self):
        item = self.list_widget.currentItem()
        if not item:
            return
        conv_id = item.data(Qt.UserRole)
        confirm = QMessageBox.question(
            self,
            "Excluir Conversa",
            f"Deseja excluir a conversa '{item.text()}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self.delete_conversation_requested.emit(conv_id)