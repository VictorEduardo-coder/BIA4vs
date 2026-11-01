from config.settings import COLORS

MAIN_STYLESHEET = f"""
QMainWindow, QWidget {{
    background-color: {COLORS['bg_primary']};
    color: {COLORS['text_primary']};
    font-family: 'Segoe UI', 'Inter', 'Ubuntu', 'Roboto', sans-serif;
    font-size: 14px;
}}

QFrame#HeaderFrame {{
    background-color: {COLORS['bg_secondary']};
    border-bottom: 1px solid {COLORS['panel']};
}}

QFrame#SidebarFrame {{
    background-color: {COLORS['bg_secondary']};
    border-right: 1px solid {COLORS['panel']};
}}

QFrame#FooterFrame {{
    background-color: {COLORS['bg_secondary']};
    border-top: 1px solid {COLORS['panel']};
}}

QListWidget {{
    background-color: {COLORS['bg_secondary']};
    border: none;
    color: {COLORS['text_primary']};
    outline: none;
}}

QListWidget::item {{
    padding: 10px;
    border-radius: 6px;
    margin: 2px 6px;
}}

QListWidget::item:selected {{
    background-color: {COLORS['panel']};
    color: {COLORS['cyan']};
}}

QListWidget::item:hover {{
    background-color: {COLORS['input_bg']};
}}

QTextEdit#PromptInput {{
    background-color: {COLORS['input_bg']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['panel']};
    border-radius: 8px;
    padding: 8px;
}}

QTextEdit#PromptInput:focus {{
    border: 1px solid {COLORS['blue_primary']};
}}

QPushButton {{
    background-color: {COLORS['panel']};
    color: {COLORS['text_primary']};
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}}

QPushButton:hover {{
    background-color: {COLORS['blue_secondary']};
}}

QPushButton#PrimaryButton {{
    background-color: {COLORS['blue_primary']};
    color: {COLORS['text_primary']};
}}

QPushButton#PrimaryButton:hover {{
    background-color: {COLORS['blue_secondary']};
}}

QPushButton#DangerButton {{
    background-color: {COLORS['panel']};
    color: {COLORS['error']};
}}

QScrollArea {{
    border: none;
    background-color: {COLORS['bg_primary']};
}}

QScrollBar:vertical {{
    background: {COLORS['bg_primary']};
    width: 8px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS['panel']};
    min-height: 24px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical:hover {{
    background: {COLORS['blue_secondary']};
}}
"""