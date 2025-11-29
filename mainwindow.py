import logging

from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QMessageBox, QGridLayout, QDialog, QTextEdit)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from database import DatabaseManager
from dialogs import ConnectionDialog,AddFinanceDialog,  EditFinanceDialog, LoggerDialog, DataViewDialog, AddDataDialog, AddPointDialog, AddEmployeeDialog, AddProductDialog
from styles import STYLES
from advanced_features import ( TextSearchDialog,
    StringFunctionsDialog
)
from select import AdvancedSelectDialog
from alter import AlterTableDialog
from typesdialog import UserTypesDialog
from viewsdialog import ViewsDialog
from cte_builder import CteBuilderDialog



class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.db_manager = DatabaseManager()
        self.setWindowTitle("Система управления 'Крошка Картошка'")
        self.setMinimumSize(900, 650)
        self.setup_ui()
        self.apply_styles()

    def apply_styles(self):
        self.setStyleSheet(STYLES)

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        title = QLabel("Крошка Картошка - Система управления")
        title.setAlignment(Qt.AlignCenter)
        title.setObjectName("title")
        title.setFont(QFont("Arial", 60, QFont.Bold))
        layout.addWidget(title)

        # Создаем два ряда кнопок
        grid_layout1 = QGridLayout()
        grid_layout1.setSpacing(15)
        grid_layout1.setContentsMargins(20, 20, 20, 20)

        # Первый ряд - основные функции
        buttons_info1 = [
            ("Логи", self.show_logger, 0, 0),
            ("Подключение к БД", self.show_connection_dialog, 0, 1),
            ("Добавить данные", self.show_add_data, 1, 0),
            ("Просмотр данных", self.show_view_data, 1, 1),
            ("О программе", self.show_about, 2, 1),
            ("Пользовательские типы", self.show_types_data, 2,0)
        ]

        for text, slot, row, col in buttons_info1:
            btn = QPushButton(text)
            btn.setObjectName("primary")
            btn.clicked.connect(slot)
            btn.setMinimumHeight(60)
            btn.setMinimumWidth(180)
            grid_layout1.addWidget(btn, row, col)

        layout.addLayout(grid_layout1)

        # Второй ряд - расширенные функции (новые)
        grid_layout2 = QGridLayout()
        grid_layout2.setSpacing(10)
        grid_layout2.setContentsMargins(20, 10, 20, 20)

        advancedbuttonsinfo = [
            ("ALTER TABLE", self.open_alter_table, 0, 0),
            ("SELECT", self.open_advanced_select, 0, 1),
            ("VIEWS", self.openviews, 0, 2),
            ("CTE", self.opencte, 1, 0),
            ("Текстовый поиск", self.open_text_search, 1, 1),
            ("Строковые функции", self.open_string_functions, 1, 2),
        ]

        for text, slot, row, col in advancedbuttonsinfo:
            btn = QPushButton(text)
            btn.setObjectName("primary")
            btn.clicked.connect(slot)
            btn.setMinimumHeight(50)
            btn.setMinimumWidth(160)
            grid_layout2.addWidget(btn, row, col)

        layout.addLayout(grid_layout2)

        self.status_label = QLabel("Статус: Не подключено к БД")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Arial", 10))
        layout.addWidget(self.status_label)

        self.update_status()

    def update_status(self):
        try:
            if self.db_manager.is_connected():
                self.status_label.setText("Статус: Подключено к БД")
                self.status_label.setStyleSheet("color: #90cb25; font-weight: bold;")
            else:
                self.status_label.setText("Статус: Не подключено к БД")
                self.status_label.setStyleSheet("color: #d9534f; font-weight: bold;")
        except:
            self.status_label.setText("Ошибка проверки статуса")
            self.status_label.setStyleSheet("color: #d9534f; font-weight: bold;")

    def show_logger(self):
        dialog = LoggerDialog(self.db_manager, self)
        dialog.exec()

    def show_connection_dialog(self):
        dialog = ConnectionDialog(self.db_manager, self)
        dialog.exec()
        self.update_status()

    def show_add_data(self):
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
            elif data_type == 'finances':
                self.add_finance()

    def show_view_data(self):
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к базе данных")
            return
        
        dialog = DataViewDialog(self.db_manager, self)
        dialog.exec()

    def show_types_data(self):
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к базе данных")
            return

        dialog = UserTypesDialog(self.db_manager, self)
        dialog.exec()

    def refresh_all(self):
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к базе данных")
            return
        
        try:
            points_count = self.db_manager.get_points_count()
            employees_count = self.db_manager.get_employees_count()
            products_count = self.db_manager.get_products_count()
            total_revenue = self.db_manager.get_total_revenue()
            total_expenses = self.db_manager.get_total_expenses()
            profit = total_revenue - total_expenses
            
            data_exists = self.db_manager.check_data_exists()

            stats_text = f"""
            <h2>📊 Статистика системы</h2>
            
            <h3>Основные показатели:</h3>
            <ul>
                <li><b>Количество точек:</b> {points_count}</li>
                <li><b>Количество сотрудников:</b> {employees_count}</li>
                <li><b>Количество продуктов:</b> {products_count}</li>
                <li><b>Общий доход:</b> {total_revenue:,.2f} руб.</li>
                <li><b>Общие расходы:</b> {total_expenses:,.2f} руб.</li>
                <li><b>Прибыль:</b> <span style='color: {'#90cb25' if profit >= 0 else '#d9534f'}'>{profit:,.2f} руб.</span></li>
            </ul>
            
            <h3>Наличие данных в таблицах:</h3>
            <ul>
                <li>Точки: {'Есть данные' if data_exists['points'] else 'Нет данных'}</li>
                <li>Сотрудники: {'Есть данные' if data_exists['employees'] else 'Нет данных'}</li>
                <li>Продукты: {'Есть данные' if data_exists['products'] else 'Нет данных'}</li>
                <li>Финансы: {'Есть данные' if data_exists['transactions'] else 'Нет данных'}</li>
            </ul>
            
            <p style='color: #fda601; font-weight: bold;'>
            Статистика обновлена: {self.db_manager.get_connection_params()['host']}
            </p>
            """
            
            dialog = QDialog(self)
            dialog.setWindowTitle("Статистика системы")
            dialog.setMinimumSize(500, 600)
            
            layout = QVBoxLayout()

            stats_label = QLabel(stats_text)
            stats_label.setWordWrap(True)
            stats_label.setTextFormat(Qt.RichText)

            logs_label = QLabel("<h3>Последние действия в системе:</h3>")
            logs_text = QTextEdit()
            logs_text.setReadOnly(True)
            logs_text.setMaximumHeight(150)

            logs = self.db_manager.get_logs()
            recent_logs = ''.join(logs[-5:]) if logs else "Логи не найдены"
            logs_text.setPlainText(recent_logs)

            close_btn = QPushButton("Закрыть")
            close_btn.clicked.connect(dialog.accept)
            
            layout.addWidget(stats_label)
            layout.addWidget(logs_label)
            layout.addWidget(logs_text)
            layout.addWidget(close_btn)
            
            dialog.setLayout(layout)
            dialog.exec()
            
        except Exception as e:
            logging.error(f"Ошибка получения статистики: {str(e)}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить статистику: {str(e)}")

    def show_about(self):
        about_text = """
        <h2>Крошка Картошка</h2>
        <p><b>Система управления ресторанами быстрого питания</b></p>
        
        <p>Версия: 1.0</p>
        <p>Разработчик: Команда Крошка Картошка</p>
        
        <p>Функциональность:</p>
        <ul>
            <li>Управление точками продаж</li>
            <li>Учет сотрудников</li>
            <li>Управление продуктами</li>
            <li>Финансовый учет</li>
        </ul>
        
        <p style='color: #90cb25;'>Цветовая схема: Бренд Крошка Картошка</p>
        """
        QMessageBox.about(self, "О программе", about_text)

    def add_point(self):
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
                
    def add_finance(self):
        dialog = AddFinanceDialog(self.db_manager, self)
        if dialog.exec() == QDialog.Accepted:
            data = dialog.get_data()
            if all([data['point_id'], data['amount'], data['date']]):
                try:
                    point_id = int(data['point_id'])
                    amount = float(data['amount'])
                    
                    # Проверка формата даты (базовая)
                    if len(data['date']) != 10 or data['date'][4] != '-' or data['date'][7] != '-':
                        QMessageBox.warning(self, "Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД")
                        return
                    
                    if self.db_manager.insert_transaction(point_id, data['type'], amount, data['date'], data['description']):
                        QMessageBox.information(self, "Успех", "Финансовая операция успешно добавлена!")
                    else:
                        QMessageBox.warning(self, "Ошибка", "Ошибка при добавлении финансовой операции")
                except ValueError:
                    QMessageBox.warning(self, "Ошибка", "ID точки и сумма должны быть числами")
            else:
                QMessageBox.warning(self, "Ошибка", "Поля с * обязательны для заполнения")

    def open_alter_table(self):
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к базе данных")
            return
        dialog = AlterTableDialog(self.db_manager, self)
        dialog.exec()

    def open_advanced_select(self):
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к базе данных")
            return
        dialog = AdvancedSelectDialog(self.db_manager, self)
        dialog.exec()

    def open_text_search(self):
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к базе данных")
            return
        dialog = TextSearchDialog(self.db_manager, self)
        dialog.exec()

    def open_string_functions(self):
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Ошибка", "Сначала подключитесь к базе данных")
            return
        dialog = StringFunctionsDialog(self.db_manager, self)
        dialog.exec()
    def openviews(self):
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Нет подключения", "Сначала подключитесь к базе данных.")
            return
        dialog = ViewsDialog(self.db_manager, self)
        dialog.exec()

    def opencte(self):
        if not self.db_manager.is_connected():
            QMessageBox.warning(self, "Нет подключения", "Сначала подключитесь к базе данных.")
            return
        dialog = CteBuilderDialog(self.db_manager, self)
        dialog.exec()

