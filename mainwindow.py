from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QGridLayout, QDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database import DatabaseManager
from dialogs import ConnectionDialog, LoggerDialog, DataViewDialog, AddDataDialog, AddPointDialog, AddEmployeeDialog, AddProductDialog
from styles import STYLES

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.setWindowTitle("🍟 Система управления 'Крошка Картошка'")
        self.setMinimumSize(900, 700)
        self.setup_ui()
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet(STYLES)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Заголовок
        title = QLabel("🍟 Крошка Картошка - Система управления")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")
        title.setFont(QFont("Arial", 18, QFont.Bold))
        layout.addWidget(title)

        # # Подзаголовок
        # subtitle = QLabel("Управление ресторанами быстрого питания")
        # subtitle.setAlignment(Qt.AlignCenter)
        # subtitle.setFont(QFont("Arial", 12))
        # layout.addWidget(subtitle)

        # layout.addSpacing(20)

        # Сетка кнопок меню
        grid_layout = QGridLayout()
        grid_layout.setSpacing(15)
        grid_layout.setContentsMargins(20, 20, 20, 20)

        # Создаем кнопки меню с более короткими текстами
        buttons_info = [
            ("📊 Логи", self.show_logger, 0, 0),
            ("🔌 Подключение к БД", self.show_connection_dialog, 0, 1),
            ("➕ Добавить данные", self.show_add_data, 1, 0),
            ("👀 Просмотр данных", self.show_view_data, 1, 1),
            ("🔄 Обновить", self.refresh_all, 2, 0),
            ("ℹ️ О программе", self.show_about, 2, 1)
        ]

        for text, slot, row, col in buttons_info:
            btn = QPushButton(text)
            btn.setObjectName("primary")
            btn.clicked.connect(slot)
            btn.setMinimumHeight(60)
            btn.setMinimumWidth(180)
            grid_layout.addWidget(btn, row, col)

        layout.addLayout(grid_layout)

        # Статус бар
        self.status_label = QLabel("Статус: Не подключено к БД")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_label)

        # Обновляем статус
        self.update_status()

    def update_status(self):
        try:
            if self.db_manager.is_connected():
                self.status_label.setText("🌞 Статус: Подключено к БД")
                self.status_label.setStyleSheet("color: #90cb25; font-weight: bold;")
            else:
                self.status_label.setText("😔 Статус: Не подключено к БД")
                self.status_label.setStyleSheet("color: #d9534f; font-weight: bold;")
        except:
            self.status_label.setText("😠 Ошибка проверки статуса")
            self.status_label.setStyleSheet("color: #d9534f; font-weight: bold;")

    def show_logger(self):
        dialog = LoggerDialog(self.db_manager, self)
        dialog.exec()

    def show_connection_dialog(self):
        dialog = ConnectionDialog(self.db_manager, self)
        dialog.exec()
        self.update_status()

    def show_add_data(self):
        """Диалог для добавления данных"""
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к базе данных")
            return
        
        dialog = AddDataDialog(self.db_manager, self)
        if dialog.exec() == QDialog.Accepted:
            data_type = dialog.get_data_type()
            if data_type == 'point':
                self.add_point()
            elif data_type == 'employee':
                self.add_employee()
            elif data_type == 'product':
                self.add_product()

    def show_view_data(self):
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к базе данных")
            return
        
        dialog = DataViewDialog(self.db_manager, self)
        dialog.exec()

    def refresh_all(self):
        self.update_status()
        QMessageBox.information(self, "Обновление", "Статус обновлен")

    def show_about(self):
        about_text = """
        <h2>🍟 Крошка Картошка</h2>
        <p><b>Система управления ресторанами быстрого питания</b></p>
        
        <p>Версия: 1.0</p>
        <p>Разработчик: Команда Крошка Картошка</p>
        
        <p>Функциональность:</p>
        <ul>
            <li>Управление точками продаж</li>
            <li>Учет сотрудников</li>
            <li>Управление продуктами</li>
            <li>Финансовый учет</li>
            <li>Учет поставок</li>
        </ul>
        
        <p style='color: #90cb25;'>Цветовая схема: Бренд Крошка Картошка</p>
        """
        QMessageBox.about(self, "О программе", about_text)

    def add_point(self):
        """Добавляет точку"""
        dialog = AddPointDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if data['address']:
                if self.db_manager.insert_point(data['address'], data['phone']):
                    QMessageBox.information(self, "Успех", "Точка успешно добавлена!")
                else:
                    QMessageBox.warning(self, "Ошибка", "Ошибка при добавлении точки")
            else:
                QMessageBox.warning(self, "Ошибка", "Адрес обязателен для заполнения")

    def add_employee(self):
        """Добавляет сотрудника"""
        dialog = AddEmployeeDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if all([data['full_name'], data['position'], data['salary'], data['schedule'], data['point_id']]):
                try:
                    salary = float(data['salary'])
                    point_id = int(data['point_id'])
                    if self.db_manager.insert_employee(data['full_name'], data['position'], salary, data['schedule'], point_id):
                        QMessageBox.information(self, "Успех", "Сотрудник успешно добавлен!")
                    else:
                        QMessageBox.warning(self, "Ошибка", "Ошибка при добавлении сотрудника")
                except ValueError:
                    QMessageBox.warning(self, "Ошибка", "Зарплата и ID точки должны быть числами")
            else:
                QMessageBox.warning(self, "Ошибка", "Все поля обязательны для заполнения")

    def add_product(self):
        """Добавляет продукт"""
        dialog = AddProductDialog(self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if all([data['name'], data['category'], data['cost_price'], data['selling_price']]):
                try:
                    cost_price = float(data['cost_price'])
                    selling_price = float(data['selling_price'])
                    if self.db_manager.insert_product(data['name'], data['category'], cost_price, selling_price):
                        QMessageBox.information(self, "Успех", "Продукт успешно добавлен!")
                    else:
                        QMessageBox.warning(self, "Ошибка", "Ошибка при добавлении продукта")
                except ValueError:
                    QMessageBox.warning(self, "Ошибка", "Цены должны быть числами")
            else:
                QMessageBox.warning(self, "Ошибка", "Все поля обязательны для заполнения")