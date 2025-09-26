from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QTabWidget, QWidget, QGroupBox, QMessageBox)
from PySide6.QtCore import Qt
import logging

class ConnectionDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Подключение к Базе Данных")
        self.setFixedSize(600, 350)
        self.setup_ui()
        self.load_current_params()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Форма ввода параметров
        form_layout = QFormLayout()

        self.host_input = QLineEdit()
        self.port_input = QLineEdit()
        self.dbname_input = QLineEdit()
        self.user_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)

        form_layout.addRow("Хост:", self.host_input)
        form_layout.addRow("Порт:", self.port_input)
        form_layout.addRow("База данных:", self.dbname_input)
        form_layout.addRow("Пользователь:", self.user_input)
        form_layout.addRow("Пароль:", self.password_input)

        layout.addLayout(form_layout)

        # Кнопки действий
        buttons_layout = QHBoxLayout()

        self.connect_btn = QPushButton("Подключиться")
        self.recreate_btn = QPushButton("Пересоздать таблицы")
        self.env_btn = QPushButton("Взять из окружения")

        self.connect_btn.clicked.connect(self.connect)
        self.recreate_btn.clicked.connect(self.recreate_tables)
        self.env_btn.clicked.connect(self.load_from_env)

        buttons_layout.addWidget(self.connect_btn)
        buttons_layout.addWidget(self.recreate_btn)
        buttons_layout.addWidget(self.env_btn)

        layout.addLayout(buttons_layout)

        # Статус
        self.status_label = QLabel("😔 Не подключено")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #d9534f; font-weight: bold;")
        layout.addWidget(self.status_label)

        self.setLayout(layout)

    def load_current_params(self):
        params = self.db_manager.get_connection_params()
        self.host_input.setText(params.get('host', 'localhost'))
        self.port_input.setText(params.get('port', '5432'))
        self.dbname_input.setText(params.get('dbname', 'postgres'))
        self.user_input.setText(params.get('user', 'postgres'))
        self.password_input.setText(params.get('password', ''))

    def connect(self):
        params = {
            'host': self.host_input.text(),
            'port': self.port_input.text(),
            'dbname': self.dbname_input.text(),
            'user': self.user_input.text(),
            'password': self.password_input.text()
        }

        self.db_manager.set_connection_params(params)

        if self.db_manager.connect():
            self.status_label.setText("🌞 Подключено успешно")
            self.status_label.setStyleSheet("color: #90cb25; font-weight: bold;")
        else:
            self.status_label.setText("😠 Ошибка подключения")
            self.status_label.setStyleSheet("color: #d9534f; font-weight: bold;")

    def recreate_tables(self):
        """Открывает диалог выбора действия с таблицами"""
        dialog = RecreateTablesDialog(self.db_manager, self)
        if dialog.exec() == QDialog.Accepted:
            action_type = dialog.get_action_type()
            
            if action_type == 'дщф':
                self.clear_tables_action()
            elif action_type == 'sample_data':
                self.sample_data_action()
            elif action_type == 'recreate':
                self.recreate_tables_action()

    def clear_tables_action(self):
        """Очищает таблицы"""
        if self.db_manager.clear_tables():
            QMessageBox.information(self, "Успех", "Таблицы успешно очищены")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось очистить таблицы")

    def sample_data_action(self):
        """Вставляет тестовые данные"""
        if self.db_manager.insert_sample_data():
            QMessageBox.information(self, "Успех", "Тестовые данные успешно добавлены")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить тестовые данные")

    def recreate_tables_action(self):
        """Полностью пересоздает таблицы"""
        if self.db_manager.recreate_tables():
            QMessageBox.information(self, "Успех", "Таблицы успешно пересозданы")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось пересоздать таблицы")

    def load_from_env(self):
        self.db_manager.load_from_environment()
        self.load_current_params()
        self.status_label.setText("Параметры загружены из окружения")

class LoggerDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Логи приложения")
        self.setMinimumSize(600, 400)
        self.setup_ui()
        self.load_logs()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setObjectName("Logger")

        refresh_btn = QPushButton("Обновить логи")
        refresh_btn.clicked.connect(self.load_logs)

        layout.addWidget(QLabel("Логи приложения:"))
        layout.addWidget(self.log_text)
        layout.addWidget(refresh_btn)

        self.setLayout(layout)

    def load_logs(self):
        logs = self.db_manager.get_logs()
        self.log_text.setPlainText(''.join(logs[-100:]))

class DataViewDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Просмотр данных")
        self.setMinimumSize(800, 600)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.tabs = QTabWidget()

        # Создаем вкладки для каждой таблицы
        self.points_tab = self.create_table_tab("Точки", ["ID", "Адрес", "Телефон", "Менеджер ID"])
        self.employees_tab = self.create_table_tab("Сотрудники", ["ID", "ФИО", "Должность", "Зарплата", "График", "Точка ID"])
        self.products_tab = self.create_table_tab("Продукты", ["ID", "Название", "Категория", "Себестоимость", "Цена продажи"])
        self.finances_tab = self.create_table_tab("Финансы", ["ID", "Точка ID", "Тип", "Сумма", "Дата", "Описание"])
        self.supplies_tab = self.create_table_tab("Поставки", ["ID", "Продукт ID", "Количество", "Дата поставки", "Срок годности"])

        self.tabs.addTab(self.points_tab, "Точки")
        self.tabs.addTab(self.employees_tab, "Сотрудники")
        self.tabs.addTab(self.products_tab, "Продукты")
        self.tabs.addTab(self.finances_tab, "Финансы")
        self.tabs.addTab(self.supplies_tab, "Поставки")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def create_table_tab(self, title, headers):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(QLabel(f"Таблица: {title}"))
        layout.addWidget(table)
        
        return widget

    def load_data(self):
        """Загружает данные в таблицы"""
        try:
            # Получаем все таблицы
            for i in range(self.tabs.count()):
                tab_widget = self.tabs.widget(i)
                table = tab_widget.findChild(QTableWidget)
                if table:
                    if i == 0:
                        data = self.db_manager.get_points()
                    elif i == 1:
                        data = self.db_manager.get_employees()
                    elif i == 2:
                        data = self.db_manager.get_products()
                    elif i == 3:
                        data = self.db_manager.get_finances()
                    elif i == 4:
                        data = self.db_manager.get_supplies()
                    else:
                        data = []
                    
                    self.load_table_data(table, data)
                    
        except Exception as e:
            logging.error(f"Ошибка загрузки данных: {str(e)}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

    def load_table_data(self, table, data):
        if not data:
            table.setRowCount(1)
            table.setItem(0, 0, QTableWidgetItem("Нет данных"))
            return
            
        table.setRowCount(len(data))
        for row_idx, row_data in enumerate(data):
            for col_idx, cell_data in enumerate(row_data):
                item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

class AddDataDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Добавить данные")
        self.setFixedSize(300, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        label = QLabel("Выберите тип данных для добавления:")
        layout.addWidget(label)

        self.point_btn = QPushButton("➕ Добавить точку")
        self.employee_btn = QPushButton("👨‍💼 Добавить сотрудника")
        self.product_btn = QPushButton("🍟 Добавить продукт")
        self.finances_btn = QPushButton("💰 Добавить финансовую операцию")
        self.supplies_btn = QPushButton("🚚💨 Добавить поставку")

        self.point_btn.clicked.connect(lambda: self.accept_with_type('point'))
        self.employee_btn.clicked.connect(lambda: self.accept_with_type('employee'))
        self.product_btn.clicked.connect(lambda: self.accept_with_type('product'))
        self.finances_btn.clicked.connect(lambda: self.accept_with_type('finances'))
        self.supplies_btn.clicked.connect(lambda: self.accept_with_type('supplies'))

        layout.addWidget(self.point_btn)
        layout.addWidget(self.employee_btn)
        layout.addWidget(self.product_btn)
        layout.addWidget(self.finances_btn)
        layout.addWidget(self.supplies_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)
        self.data_type = None

    def accept_with_type(self, data_type):
        self.data_type = data_type
        super().accept()

    def get_data_type(self):
        return self.data_type

class AddPointDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить точку")
        self.setFixedSize(400, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.address_input = QLineEdit()
        self.phone_input = QLineEdit()

        form_layout.addRow("Адрес:*", self.address_input)
        form_layout.addRow("Телефон:", self.phone_input)

        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.cancel_btn = QPushButton("Отмена")

        self.add_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_data(self):
        return {
            'address': self.address_input.text().strip(),
            'phone': self.phone_input.text().strip() or None
        }

class AddEmployeeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить сотрудника")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.position_input = QLineEdit()
        self.salary_input = QLineEdit()
        self.schedule_input = QLineEdit()
        self.point_id_input = QLineEdit()

        form_layout.addRow("ФИО:*", self.name_input)
        form_layout.addRow("Должность:*", self.position_input)
        form_layout.addRow("Зарплата:*", self.salary_input)
        form_layout.addRow("График:*", self.schedule_input)
        form_layout.addRow("ID точки:*", self.point_id_input)

        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.cancel_btn = QPushButton("Отмена")

        self.add_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_data(self):
        return {
            'full_name': self.name_input.text().strip(),
            'position': self.position_input.text().strip(),
            'salary': self.salary_input.text().strip(),
            'schedule': self.schedule_input.text().strip(),
            'point_id': self.point_id_input.text().strip()
        }
    
class AddProductDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить продукт")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.category_input = QLineEdit()
        self.cost_input = QLineEdit()
        self.price_input = QLineEdit()

        form_layout.addRow("Название:*", self.name_input)
        form_layout.addRow("Категория:*", self.category_input)
        form_layout.addRow("Себестоимость:*", self.cost_input)
        form_layout.addRow("Цена продажи:*", self.price_input)

        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.cancel_btn = QPushButton("Отмена")

        self.add_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.add_btn)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_data(self):
        return {
            'name': self.name_input.text().strip(),
            'category': self.category_input.text().strip(),
            'cost_price': self.cost_input.text().strip(),
            'selling_price': self.price_input.text().strip()
        }
class RecreateTablesDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Управление таблицами")
        self.setFixedSize(400, 200)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        label = QLabel("Выберите действие с таблицами:")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        # Кнопки действий
        self.clear_btn = QPushButton("🗑️ Очистить таблицы (удалить все данные)")
        self.sample_data_btn = QPushButton("📊 Вставить тестовые данные")
        self.recreate_btn = QPushButton("🔄 Полностью пересоздать таблицы")

        self.clear_btn.clicked.connect(lambda: self.accept_with_action('clear'))
        self.sample_data_btn.clicked.connect(lambda: self.accept_with_action('sample_data'))
        self.recreate_btn.clicked.connect(lambda: self.accept_with_action('recreate'))

        layout.addWidget(self.clear_btn)
        layout.addWidget(self.sample_data_btn)
        layout.addWidget(self.recreate_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        layout.addWidget(cancel_btn)

        self.setLayout(layout)
        self.action_type = None

    def accept_with_action(self, action_type):
        self.action_type = action_type
        super().accept()

    def get_action_type(self):
        return self.action_type