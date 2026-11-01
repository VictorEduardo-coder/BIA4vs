from PyQt5.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt
from config.settings import COLORS


class HeaderWidget(QFrame):
    STATUS_COLORS = {
        "Online": COLORS["success"],
        "Conectando": COLORS["warning"],
        "Processando": COLORS["cyan"],
        "Desconectado": COLORS["error"]
    }

    def __init__(self):
        super().__init__()
        self.setObjectName("HeaderFrame")
        self.setFixedHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 8, 20, 8)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)

        self.title_label = QLabel("BIA4vs")
        self.title_label.setStyleSheet(
            f"font-size: 18px; font-weight: 700; color: {COLORS['text_primary']};"
        )

        self.subtitle_label = QLabel("Assistente de Pesquisa e Análise de Código")
        self.subtitle_label.setStyleSheet(
            f"font-size: 12px; color: {COLORS['text_secondary']};"
        )

        title_box.addWidget(self.title_label)
        title_box.addWidget(self.subtitle_label)

        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.set_status("Online")

        layout.addLayout(title_box)
        layout.addStretch()
        layout.addWidget(self.status_label)

    def set_status(self, state):
        color = self.STATUS_COLORS.get(state, COLORS["text_secondary"])
        self.status_label.setText(
            f"<span style='color:{color}; font-size:14px;'>●</span> "
            f"<span style='color:{COLORS['text_primary']}; font-size:13px;'>{state}</span>"
        )