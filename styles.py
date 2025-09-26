STYLES = """
QMainWindow {
    background-color: #fefdfb;
}

QWidget {
    background-color: #fefdfb;
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 10pt;
}

/* Основные кнопки */
QPushButton {
    background-color: #fda601;
    border: 2px solid #3d1908;
    color: #3d1908;
    padding: 8px 16px;
    border-radius: 6px;
    font-weight: bold;
    font-size: 10pt;
    min-height: 35px;
    min-width: 120px;
}


QPushButton:hover {
    background-color: #ffebb8;
    border-color: #fda601;
}

QPushButton:pressed {
    background-color: #90cb25;
    color: #fefdfb;
}

QPushButton:disabled {
    background-color: #cccccc;
    color: #666666;
}

/* Специальные кнопки */
QPushButton#primary {
    background-color: #90cb25;
    color: #fefdfb;
    font-size: 10pt;
    padding: 10px 20px;
    min-height: 60px;
    min-width: 180px;
}

QPushButton#primary:hover {
    background-color: #a8d64c;
}

QPushButton#danger {
    background-color: #d9534f;
    color: #fefdfb;
}

QPushButton#success {
    background-color: #90cb25;
    color: #fefdfb;
}

/* Поля ввода */
QLineEdit, QComboBox, QSpinBox, QDoubleSpinBox, QTextEdit {
    background-color: #ffebb8;
    border: 2px solid #fda601;
    border-radius: 6px;
    padding: 8px;
    font-size: 10pt;
    color: #3d1908;
    selection-background-color: #90cb25;
}

QLineEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #90cb25;
    background-color: #fefdfb;
}

/* Метки */
QLabel {
    color: #3d1908;
    font-weight: bold;
    padding: 5px;
}

QLabel#title {
    font-size: 16pt;
    font-weight: bold;
    color: #3d1908;
    background-color: #ffebb8;
    padding: 15px;
    border-radius: 8px;
    border: 2px solid #fda601;
}

/* Таблицы */
QTableWidget {
    background-color: #fefdfb;
    gridline-color: #fda601;
    border: 2px solid #fda601;
    border-radius: 6px;
    alternate-background-color: #ffebb8;
}

QTableWidget::item {
    padding: 10px;
    border-bottom: 1px solid #fda601;
    color: #3d1908;
}

QTableWidget::item:selected {
    background-color: #90cb25;
    color: #fefdfb;
}

QHeaderView::section {
    background-color: #fda601;
    color: #3d1908;
    padding: 12px;
    border: none;
    font-weight: bold;
    font-size: 10pt;
}

/* Вкладки */
QTabWidget::pane {
    border: 2px solid #fda601;
    border-radius: 8px;
    background-color: #fefdfb;
    margin-top: 10px;
}

QTabBar::tab {
    background-color: #ffebb8;
    color: #3d1908;
    padding: 12px 24px;
    margin-right: 2px;
    border-top-left-radius: 8px;
    border-top-right-radius: 8px;
    font-weight: bold;
}

QTabBar::tab:selected {
    background-color: #fda601;
    color: #3d1908;
}

QTabBar::tab:hover:!selected {
    background-color: #90cb25;
    color: #fefdfb;
}

/* Группы */
QGroupBox {
    font-weight: bold;
    color: #3d1908;
    border: 2px solid #fda601;
    border-radius: 8px;
    margin-top: 15px;
    padding-top: 15px;
    background-color: #ffebb8;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    background-color: #fda601;
    color: #3d1908;
    padding: 8px 20px;
    border-radius: 4px;
    margin-top: -10px;
}

/* Диалоги */
QDialog {
    background-color: #fefdfb;
}

QMessageBox {
    background-color: #fefdfb;
}

QTextEdit#Logger {
    background-color: #3d1908;
    color: #90cb25;
    font-family: "Courier New", monospace;
    font-size: 9pt;
    border: 2px solid #fda601;
    border-radius: 6px;
}

/* Скроллбары */
QScrollBar:vertical {
    background-color: #ffebb8;
    width: 15px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #fda601;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #90cb25;
}
# /* Кнопка редактирования в таблицах */
# QPushButton[text="✏️ Редактировать"] {
#     background-color: #90cb25; 
#     color: white;
#     font-weight: bold;
# }

# QPushButton[text="✏️ Редактировать"]:hover {
#     background-color: #a8d64c;
# }

# QPushButton[text="✏️ Редактировать"]:pressed {
#     background-color: #7bb322;
# }
# """