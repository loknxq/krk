from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QWidget, QGroupBox, QInputDialog)
from PySide6.QtCore import Qt
import logging

class EditDataDialog(QDialog):
    def __init__(self, db_manager, table_name, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.table_name = table_name
        self.setWindowTitle(f"Редактирование - {table_name}")
        self.setFixedSize(300, 250)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        label = QLabel(f"Выберите действие для таблицы '{self.table_name}':")
        layout.addWidget(label)

        self.edit_btn = QPushButton("Изменить строку")
        self.delete_btn = QPushButton("Удалить строку")
        self.cancel_btn = QPushButton("Отмена")

        self.edit_btn.clicked.connect(self.edit_row)
        self.delete_btn.clicked.connect(self.delete_row)
        self.cancel_btn.clicked.connect(self.reject)

        layout.addWidget(self.edit_btn)
        layout.addWidget(self.delete_btn)
        layout.addWidget(self.cancel_btn)

        self.setLayout(layout)

    def edit_row(self):
        id, ok = QInputDialog.getInt(self, "Изменение строки", 
                                f"Введите ID строки для изменения в таблице '{self.table_name}':",
                                1, 1, 1000000, 1)
        if ok:
            self.action_type = 'edit'
            self.row_id = id
            self.accept()

    def delete_row(self):
        id, ok = QInputDialog.getInt(self, "Удаление строки",
                                f"Введите ID строки для удаления из таблицы '{self.table_name}':",
                                1, 1, 1000000, 1)
        if ok:
            self.action_type = 'delete'
            self.row_id = id
            self.accept()

    def get_action_info(self):
        return self.action_type, self.row_id

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

        buttons_layout = QHBoxLayout()

        self.connect_btn = QPushButton("Подключиться")
        self.recreate_btn = QPushButton("Управление таблицами")

        self.connect_btn.clicked.connect(self.connect)
        self.recreate_btn.clicked.connect(self.recreate_tables)

        buttons_layout.addWidget(self.connect_btn)
        buttons_layout.addWidget(self.recreate_btn)

        layout.addLayout(buttons_layout)

        self.status_label = QLabel("Не подключено")
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
            self.status_label.setText("Подключено успешно")
            self.status_label.setStyleSheet("color: #90cb25; font-weight: bold;")
        else:
            self.status_label.setText("Ошибка подключения")
            self.status_label.setStyleSheet("color: #d9534f; font-weight: bold;")

    def recreate_tables(self):
        dialog = RecreateTablesDialog(self.db_manager, self)
        if dialog.exec() == QDialog.Accepted:
            action_type = dialog.get_action_type()
            
            if action_type == 'sample_data':
                self.sample_data_action()
            elif action_type == 'recreate':
                self.recreate_tables_action()

    def sample_data_action(self):
        if self.db_manager.insert_sample_data():
            QMessageBox.information(self, "Успех", "Тестовые данные успешно добавлены")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось добавить тестовые данные")

    def recreate_tables_action(self):
        if self.db_manager.recreate_tables():
            QMessageBox.information(self, "Успех", "Таблицы успешно пересозданы")
        else:
            QMessageBox.warning(self, "Ошибка", "Не удалось пересоздать таблицы")

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
        self.setMinimumSize(900, 700)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.tabs = QTabWidget()

        self.points_tab = self.create_table_tab("Точки", ["ID", "Адрес", "Телефон", "Менеджер ID"])
        self.employees_tab = self.create_table_tab("Сотрудники", ["ID", "ФИО", "Должность", "Зарплата", "График", "Точка ID"])
        self.products_tab = self.create_table_tab("Продукты", ["ID", "Название", "Категория", "Себестоимость", "Цена продажи"])
        self.finances_tab = self.create_table_tab("Финансы", ["ID", "Точка ID", "Тип", "Сумма", "Дата", "Описание"])
        
        self.tabs.addTab(self.points_tab, "Точки")
        self.tabs.addTab(self.employees_tab, "Сотрудники")
        self.tabs.addTab(self.products_tab, "Продукты")
        self.tabs.addTab(self.finances_tab, "Финансы")

        layout.addWidget(self.tabs)
        
        refresh_btn = QPushButton("Обновить данные")
        refresh_btn.clicked.connect(self.load_data)
        layout.addWidget(refresh_btn)

        self.setLayout(layout)

    def create_table_tab(self, title, headers):
        widget = QWidget()
        layout = QVBoxLayout(widget)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"Таблица: {title}"))
        
        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(lambda: self.open_edit_dialog(title))
        header_layout.addWidget(edit_btn)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)

        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)

        layout.addWidget(table)
        
        return widget

    def open_edit_dialog(self, table_name):
        dialog = EditDataDialog(self.db_manager, table_name, self)
        if dialog.exec() == QDialog.Accepted:
            action_type, row_id = dialog.get_action_info()
            self.handle_table_action(table_name, action_type, row_id)

    def handle_table_action(self, table_name, action_type, row_id):
        try:
            if action_type == 'delete':
                success = False
                if table_name == "Точки":
                    success = self.db_manager.delete_point(row_id)
                elif table_name == "Сотрудники":
                    success = self.db_manager.delete_employee(row_id)
                elif table_name == "Продукты":
                    success = self.db_manager.delete_product(row_id)
                elif table_name == "Финансы":
                    success = self.db_manager.delete_transaction(row_id)
                
                if success:
                    QMessageBox.information(self, "Успех", f"Строка {row_id} удалена из таблицы '{table_name}'")
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось удалить строку {row_id}")
            
            elif action_type == 'edit':
                current_data = None
                if table_name == "Точки":
                    current_data = self.db_manager.get_point_by_id(row_id)
                    if current_data:
                        dialog = EditPointDialog(current_data, self)
                        if dialog.exec() == QDialog.Accepted:
                            data = dialog.get_data()
                            if data['address']:
                                if self.db_manager.update_point(row_id, data['address'], data['phone']):
                                    QMessageBox.information(self, "Успех", "Точка успешно обновлена!")
                                    self.load_data()
                                else:
                                    QMessageBox.warning(self, "Ошибка", "Ошибка при обновлении точки")
                            else:
                                QMessageBox.warning(self, "Ошибка", "Адрес обязателен для заполнения")
                    
                elif table_name == "Сотрудники":
                    current_data = self.db_manager.get_employee_by_id(row_id)
                    if current_data:
                        dialog = EditEmployeeDialog(current_data, self)
                        if dialog.exec() == QDialog.Accepted:
                            data = dialog.get_data()
                            if all([data['full_name'], data['position'], data['salary'], data['schedule'], data['point_id']]):
                                try:
                                    salary = float(data['salary'])
                                    point_id = int(data['point_id'])
                                    if self.db_manager.update_employee(row_id, data['full_name'], data['position'], salary, data['schedule'], point_id):
                                        QMessageBox.information(self, "Успех", "Сотрудник успешно обновлен!")
                                        self.load_data()
                                    else:
                                        QMessageBox.warning(self, "Ошибка", "Ошибка при обновлении сотрудника")
                                except ValueError:
                                    QMessageBox.warning(self, "Ошибка", "Зарплата и ID точки должны быть числами")
                            else:
                                QMessageBox.warning(self, "Ошибка", "Все поля обязательны для заполнения")
                    
                elif table_name == "Продукты":
                    current_data = self.db_manager.get_product_by_id(row_id)
                    if current_data:
                        dialog = EditProductDialog(current_data, self)
                        if dialog.exec() == QDialog.Accepted:
                            data = dialog.get_data()
                            if all([data['name'], data['category'], data['cost_price'], data['selling_price']]):
                                try:
                                    cost_price = float(data['cost_price'])
                                    selling_price = float(data['selling_price'])
                                    if self.db_manager.update_product(row_id, data['name'], data['category'], cost_price, selling_price):
                                        QMessageBox.information(self, "Успех", "Продукт успешно обновлен!")
                                        self.load_data()
                                    else:
                                        QMessageBox.warning(self, "Ошибка", "Ошибка при обновлении продукта")
                                except ValueError:
                                    QMessageBox.warning(self, "Ошибка", "Цены должны быть числами")
                            else:
                                QMessageBox.warning(self, "Ошибка", "Все поля обязательны для заполнения")
                    
                elif table_name == "Финансы":
                    current_data = self.db_manager.get_transaction_by_id(row_id)
                    if current_data:
                        dialog = EditFinanceDialog(current_data, self)
                        if dialog.exec() == QDialog.Accepted:
                            data = dialog.get_data()
                            if all([data['point_id'], data['amount'], data['date']]):
                                try:
                                    point_id = int(data['point_id'])
                                    amount = float(data['amount'])
                                    
                                    if len(data['date']) != 10 or data['date'][4] != '-' or data['date'][7] != '-':
                                        QMessageBox.warning(self, "Ошибка", "Дата должна быть в формате ГГГГ-ММ-ДД")
                                        return
                                    
                                    if self.db_manager.update_transaction(row_id, point_id, data['type'], amount, data['date'], data['description']):
                                        QMessageBox.information(self, "Успех", "Финансовая операция успешно обновлена!")
                                        self.load_data()
                                    else:
                                        QMessageBox.warning(self, "Ошибка", "Ошибка при обновлении финансовой операции")
                                except ValueError:
                                    QMessageBox.warning(self, "Ошибка", "ID точки и сумма должны быть числами")
                            else:
                                QMessageBox.warning(self, "Ошибка", "Поля с * обязательны для заполнения")
                    else:
                        QMessageBox.warning(self, "Ошибка", f"Финансовая операция с ID {row_id} не найдена")
                
                if not current_data and table_name != "Финансы":
                    QMessageBox.warning(self, "Ошибка", f"Запись с ID {row_id} не найдена в таблице '{table_name}'")
                    
        except Exception as e:
            logging.error(f"Ошибка обработки действия: {str(e)}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {str(e)}")

    def load_data(self):
        try:
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
                    else:
                        data = []
                    
                    self.load_table_data(table, data)
                    
        except Exception as e:
            logging.error(f"Ошибка загрузки данных: {str(e)}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные: {str(e)}")

    def load_table_data(self, table, data):
        table.verticalHeader().setDefaultSectionSize(35)
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
        self.setFixedSize(300, 370)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        label = QLabel("Выберите тип данных для добавления:")
        layout.addWidget(label)

        self.point_btn = QPushButton("Добавить точку")
        self.employee_btn = QPushButton("Добавить сотрудника")
        self.product_btn = QPushButton("Добавить продукт")
        self.finances_btn = QPushButton("Добавить финансовую операцию")

        self.point_btn.clicked.connect(lambda: self.accept_with_type('point'))
        self.employee_btn.clicked.connect(lambda: self.accept_with_type('employee'))
        self.product_btn.clicked.connect(lambda: self.accept_with_type('product'))
        self.finances_btn.clicked.connect(lambda: self.accept_with_type('finances'))

        layout.addWidget(self.point_btn)
        layout.addWidget(self.employee_btn)
        layout.addWidget(self.product_btn)
        layout.addWidget(self.finances_btn)

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
    
class AddFinanceDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Добавить финансовую операцию")
        self.setFixedSize(400, 350)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.point_id_input = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Доход", "Расход"])
        self.amount_input = QLineEdit()
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("ГГГГ-ММ-ДД")
        self.description_input = QLineEdit()

        form_layout.addRow("ID точки:*", self.point_id_input)
        form_layout.addRow("Тип:*", self.type_combo)
        form_layout.addRow("Сумма:*", self.amount_input)
        form_layout.addRow("Дата (ГГГГ-ММ-ДД):*", self.date_input)
        form_layout.addRow("Описание:", self.description_input)

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
            'point_id': self.point_id_input.text().strip(),
            'type': self.type_combo.currentText(),
            'amount': self.amount_input.text().strip(),
            'date': self.date_input.text().strip(),
            'description': self.description_input.text().strip() or None
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
        self.setFixedSize(400, 250)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        label = QLabel("Выберите действие с таблицами:")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        self.sample_data_btn = QPushButton("Вставить тестовые данные")
        self.recreate_btn = QPushButton("Пересоздать таблицы")

        self.sample_data_btn.clicked.connect(lambda: self.accept_with_action('sample_data'))
        self.recreate_btn.clicked.connect(lambda: self.accept_with_action('recreate'))

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

class EditPointDialog(QDialog):
    def __init__(self, point_data, parent=None):
        super().__init__(parent)
        self.point_data = point_data
        self.setWindowTitle("Редактирование точки")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.address_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.manager_id_input = QLineEdit()

        self.address_input.setText(self.point_data[1] if self.point_data[1] else "")
        self.phone_input.setText(self.point_data[2] if self.point_data[2] else "")
        self.manager_id_input.setText(str(self.point_data[3]) if self.point_data[3] else "")

        form_layout.addRow("Адрес:*", self.address_input)
        form_layout.addRow("Телефон:", self.phone_input)
        form_layout.addRow("Менеджер ID:", self.manager_id_input)

        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_data(self):
        return {
            'address': self.address_input.text().strip(),
            'phone': self.phone_input.text().strip() or None,
            'manager_id': self.manager_id_input.text().strip() or None
        }

class EditEmployeeDialog(QDialog):
    def __init__(self, employee_data, parent=None):
        super().__init__(parent)
        self.employee_data = employee_data
        self.setWindowTitle("Редактирование сотрудника")
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

        self.name_input.setText(self.employee_data[1] if self.employee_data[1] else "")
        self.position_input.setText(self.employee_data[2] if self.employee_data[2] else "")
        self.salary_input.setText(str(self.employee_data[3]) if self.employee_data[3] else "")
        self.schedule_input.setText(self.employee_data[4] if self.employee_data[4] else "")
        self.point_id_input.setText(str(self.employee_data[5]) if self.employee_data[5] else "")

        form_layout.addRow("ФИО:*", self.name_input)
        form_layout.addRow("Должность:*", self.position_input)
        form_layout.addRow("Зарплата:*", self.salary_input)
        form_layout.addRow("График:*", self.schedule_input)
        form_layout.addRow("ID точки:*", self.point_id_input)

        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.save_btn)
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

class EditProductDialog(QDialog):
    def __init__(self, product_data, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.setWindowTitle("Редактирование продукта")
        self.setFixedSize(400, 300)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.name_input = QLineEdit()
        self.category_input = QLineEdit()
        self.cost_input = QLineEdit()
        self.price_input = QLineEdit()

        self.name_input.setText(self.product_data[1] if self.product_data[1] else "")
        self.category_input.setText(self.product_data[2] if self.product_data[2] else "")
        self.cost_input.setText(str(self.product_data[3]) if self.product_data[3] else "")
        self.price_input.setText(str(self.product_data[4]) if self.product_data[4] else "")

        form_layout.addRow("Название:*", self.name_input)
        form_layout.addRow("Категория:*", self.category_input)
        form_layout.addRow("Себестоимость:*", self.cost_input)
        form_layout.addRow("Цена продажи:*", self.price_input)

        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.save_btn)
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
class EditFinanceDialog(QDialog):
    def __init__(self, finance_data, parent=None):
        super().__init__(parent)
        self.finance_data = finance_data
        self.setWindowTitle("Редактирование финансовой операции")
        self.setFixedSize(400, 350)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        form_layout = QFormLayout()

        self.point_id_input = QLineEdit()
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Доход", "Расход"])
        self.amount_input = QLineEdit()
        self.date_input = QLineEdit()
        self.date_input.setPlaceholderText("ГГГГ-ММ-ДД")
        self.description_input = QLineEdit()

        if self.finance_data:
            self.point_id_input.setText(str(self.finance_data[1]) if self.finance_data[1] else "")
            
            current_type = self.finance_data[2] if self.finance_data[2] else "Доход"
            index = self.type_combo.findText(current_type)
            if index >= 0:
                self.type_combo.setCurrentIndex(index)
                
            self.amount_input.setText(str(self.finance_data[3]) if self.finance_data[3] else "")
            self.date_input.setText(str(self.finance_data[4]) if self.finance_data[4] else "")
            self.description_input.setText(self.finance_data[5] if self.finance_data[5] else "")

        form_layout.addRow("ID точки:*", self.point_id_input)
        form_layout.addRow("Тип:*", self.type_combo)
        form_layout.addRow("Сумма:*", self.amount_input)
        form_layout.addRow("Дата (ГГГГ-ММ-ДД):*", self.date_input)
        form_layout.addRow("Описание:", self.description_input)

        layout.addLayout(form_layout)

        buttons_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.cancel_btn = QPushButton("Отмена")

        self.save_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.save_btn)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def get_data(self):
        return {
            'point_id': self.point_id_input.text().strip(),
            'type': self.type_combo.currentText(),
            'amount': self.amount_input.text().strip(),
            'date': self.date_input.text().strip(),
            'description': self.description_input.text().strip() or None
        }