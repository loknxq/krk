# from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
#                                QHBoxLayout, QPushButton, QTableWidget, 
#                                QTableWidgetItem, QLabel, QLineEdit, QComboBox,
#                                QSpinBox, QDoubleSpinBox, QDateEdit, QMessageBox,
#                                QDialog, QTabWidget, QGroupBox, QHeaderView,
#                                QTextEdit, QFormLayout)
# from PySide6.QtCore import Qt
# from PySide6.QtGui import QFont
# from database import DatabaseManager
# from styles import STYLES

# class AddPointDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setModal(True)
#         self.setWindowTitle("Добавить точку")
#         self.setFixedSize(400, 200)
#         self.setup_ui()
    
#     def setup_ui(self):
#         layout = QVBoxLayout()
        
#         form_layout = QFormLayout()
        
#         self.address_input = QLineEdit()
#         self.phone_input = QLineEdit()
        
#         form_layout.addRow("Адрес:", self.address_input)
#         form_layout.addRow("Телефон:", self.phone_input)
        
#         layout.addLayout(form_layout)
        
#         button_layout = QHBoxLayout()
#         self.add_button = QPushButton("Добавить")
#         self.cancel_button = QPushButton("Отмена")
        
#         self.add_button.clicked.connect(self.accept)
#         self.cancel_button.clicked.connect(self.reject)
        
#         button_layout.addWidget(self.add_button)
#         button_layout.addWidget(self.cancel_button)
        
#         layout.addLayout(button_layout)
#         self.setLayout(layout)
    
#     def get_data(self):
#         return {
#             'address': self.address_input.text(),
#             'phone': self.phone_input.text() or None
#         }

# class DeletePointDialog(QDialog):
#     def __init__(self, parent=None):
#         super().__init__(parent)
#         self.setModal(True)
#         self.setWindowTitle("Удалить точку")
#         self.setFixedSize(300, 150)
#         self.setup_ui()
    
#     def setup_ui(self):
#         layout = QVBoxLayout()
        
#         self.point_id_input = QSpinBox()
#         self.point_id_input.setMinimum(1)
#         self.point_id_input.setMaximum(1000)
        
#         form_layout = QFormLayout()
#         form_layout.addRow("ID точки для удаления:", self.point_id_input)
        
#         layout.addLayout(form_layout)
        
#         button_layout = QHBoxLayout()
#         self.delete_button = QPushButton("Удалить")
#         self.cancel_button = QPushButton("Отмена")
        
#         self.delete_button.clicked.connect(self.accept)
#         self.cancel_button.clicked.connect(self.reject)
        
#         button_layout.addWidget(self.delete_button)
#         button_layout.addWidget(self.cancel_button)
        
#         layout.addLayout(button_layout)
#         self.setLayout(layout)
    
#     def get_point_id(self):
#         return self.point_id_input.value()

# class DataViewDialog(QDialog):
#     def __init__(self, title, headers, data, parent=None):
#         super().__init__(parent)
#         self.setModal(True)
#         self.setWindowTitle(title)
#         self.setMinimumSize(800, 600)
#         self.setup_ui(headers, data)
    
#     def setup_ui(self, headers, data):
#         layout = QVBoxLayout()
        
#         self.table = QTableWidget()
#         self.table.setColumnCount(len(headers))
#         self.table.setHorizontalHeaderLabels(headers)
#         self.table.setRowCount(len(data))
        
#         for row_idx, row_data in enumerate(data):
#             for col_idx, cell_data in enumerate(row_data):
#                 item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
#                 item.setFlags(item.flags() & ~Qt.ItemIsEditable)
#                 self.table.setItem(row_idx, col_idx, item)
        
#         self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
#         layout.addWidget(self.table)
        
#         close_button = QPushButton("Закрыть")
#         close_button.clicked.connect(self.accept)
#         layout.addWidget(close_button)
        
#         self.setLayout(layout)

# class MainWindow(QMainWindow):
#     def __init__(self):
#         super().__init__()
#         self.db = DatabaseManager()
#         self.setWindowTitle("Система управления ресторанами быстрого питания")
#         self.setMinimumSize(1000, 700)
#         self.setup_ui()
#         self.apply_styles()
#         # Загружаем данные сразу при запуске
#         self.load_all_data()
    
#     def apply_styles(self):
#         self.setStyleSheet(STYLES)
    
#     def setup_ui(self):
#         central_widget = QWidget()
#         self.setCentralWidget(central_widget)
        
#         main_layout = QVBoxLayout()
#         central_widget.setLayout(main_layout)
        
#         # Заголовок
#         title_label = QLabel("Система управления ресторанами 'Крошка Картошка'")
#         title_label.setFont(QFont("Arial", 16, QFont.Bold))
#         title_label.setAlignment(Qt.AlignCenter)
#         main_layout.addWidget(title_label)
        
#         # Кнопки управления
#         control_layout = QHBoxLayout()
        
#         self.create_db_button = QPushButton("Создать схему БД")
#         self.add_point_button = QPushButton("Добавить точку")
#         self.delete_point_button = QPushButton("Удалить точку")
#         self.view_data_button = QPushButton("Показать данные")
#         self.refresh_button = QPushButton("Обновить данные")
        
#         self.create_db_button.clicked.connect(self.create_schema)
#         self.add_point_button.clicked.connect(self.show_add_point_dialog)
#         self.delete_point_button.clicked.connect(self.show_delete_point_dialog)
#         self.view_data_button.clicked.connect(self.show_data_view)
#         self.refresh_button.clicked.connect(self.load_all_data)
        
#         control_layout.addWidget(self.create_db_button)
#         control_layout.addWidget(self.add_point_button)
#         control_layout.addWidget(self.delete_point_button)
#         control_layout.addWidget(self.view_data_button)
#         control_layout.addWidget(self.refresh_button)
        
#         main_layout.addLayout(control_layout)
        
#         # Основной контент с вкладками
#         self.tab_widget = QTabWidget()
#         main_layout.addWidget(self.tab_widget)
        
#         # Создаем все вкладки
#         self.setup_points_tab()
#         self.setup_employees_tab()
#         self.setup_products_tab()
#         self.setup_finances_tab()
#         self.setup_supplies_tab()
    
#     def setup_points_tab(self):
#         points_tab = QWidget()
#         layout = QVBoxLayout()
        
#         # Список точек
#         points_group = QGroupBox("Список точек")
#         points_layout = QVBoxLayout()
        
#         self.points_table = QTableWidget()
#         self.points_table.setColumnCount(4)
#         self.points_table.setHorizontalHeaderLabels(["ID", "Адрес", "Телефон", "Менеджер"])
        
#         points_layout.addWidget(self.points_table)
#         points_group.setLayout(points_layout)
#         layout.addWidget(points_group)
        
#         points_tab.setLayout(layout)
#         self.tab_widget.addTab(points_tab, "Точки")
    
#     def setup_employees_tab(self):
#         employees_tab = QWidget()
#         layout = QVBoxLayout()
        
#         employees_group = QGroupBox("Сотрудники")
#         employees_layout = QVBoxLayout()
        
#         self.employees_table = QTableWidget()
#         self.employees_table.setColumnCount(6)
#         self.employees_table.setHorizontalHeaderLabels(["ID", "ФИО", "Должность", "Зарплата", "График", "Точка"])
        
#         employees_layout.addWidget(self.employees_table)
#         employees_group.setLayout(employees_layout)
#         layout.addWidget(employees_group)
        
#         employees_tab.setLayout(layout)
#         self.tab_widget.addTab(employees_tab, "Сотрудники")
    
#     def setup_products_tab(self):
#         products_tab = QWidget()
#         layout = QVBoxLayout()
        
#         products_group = QGroupBox("Продукты")
#         products_layout = QVBoxLayout()
        
#         self.products_table = QTableWidget()
#         self.products_table.setColumnCount(5)
#         self.products_table.setHorizontalHeaderLabels(["ID", "Название", "Категория", "Себестоимость", "Цена продажи"])
        
#         products_layout.addWidget(self.products_table)
#         products_group.setLayout(products_layout)
#         layout.addWidget(products_group)
        
#         products_tab.setLayout(layout)
#         self.tab_widget.addTab(products_tab, "Продукты")
    
#     def setup_finances_tab(self):
#         finances_tab = QWidget()
#         layout = QVBoxLayout()
        
#         finances_group = QGroupBox("Финансовые операции")
#         finances_layout = QVBoxLayout()
        
#         self.finances_table = QTableWidget()
#         self.finances_table.setColumnCount(6)
#         self.finances_table.setHorizontalHeaderLabels(["ID", "Точка", "Тип", "Сумма", "Дата", "Описание"])
        
#         finances_layout.addWidget(self.finances_table)
#         finances_group.setLayout(finances_layout)
#         layout.addWidget(finances_group)
        
#         finances_tab.setLayout(layout)
#         self.tab_widget.addTab(finances_tab, "Финансы")
    
#     def setup_supplies_tab(self):
#         supplies_tab = QWidget()
#         layout = QVBoxLayout()
        
#         supplies_group = QGroupBox("Поставки")
#         supplies_layout = QVBoxLayout()
        
#         self.supplies_table = QTableWidget()
#         self.supplies_table.setColumnCount(5)
#         self.supplies_table.setHorizontalHeaderLabels(["ID", "Продукт", "Количество", "Дата поставки", "Срок годности"])
        
#         supplies_layout.addWidget(self.supplies_table)
#         supplies_group.setLayout(supplies_layout)
#         layout.addWidget(supplies_group)
        
#         supplies_tab.setLayout(layout)
#         self.tab_widget.addTab(supplies_tab, "Поставки")
    
#     def create_schema(self):
#         try:
#             if self.db.create_schema():
#                 QMessageBox.information(self, "Успех", "Схема БД успешно создана!")
#                 # ЗАГРУЖАЕМ ДАННЫЕ ПОСЛЕ СОЗДАНИЯ СХЕМЫ
#                 self.load_all_data()
#             else:
#                 QMessageBox.warning(self, "Ошибка", "Ошибка при создании схемы БД")
#         except Exception as e:
#             QMessageBox.critical(self, "Ошибка", f"Ошибка: {str(e)}")
    
#     def show_add_point_dialog(self):
#         dialog = AddPointDialog(self)
#         if dialog.exec() == QDialog.Accepted:
#             data = dialog.get_data()
#             if data['address']:
#                 if self.db.insert_point(data['address'], data['phone']):
#                     self.load_points()  # ОБНОВЛЯЕМ ТАБЛИЦУ
#                     QMessageBox.information(self, "Успех", "Точка успешно добавлена!")
#                 else:
#                     QMessageBox.warning(self, "Ошибка", "Ошибка при добавлении точки")
    
#     def show_delete_point_dialog(self):
#         dialog = DeletePointDialog(self)
#         if dialog.exec() == QDialog.Accepted:
#             point_id = dialog.get_point_id()
#             reply = QMessageBox.question(self, "Подтверждение", 
#                                        f"Вы уверены, что хотите удалить точку с ID {point_id}?")
#             if reply == QMessageBox.Yes:
#                 if self.db.delete_point(point_id):
#                     self.load_points()  # ОБНОВЛЯЕМ ТАБЛИЦУ
#                     QMessageBox.information(self, "Успех", "Точка успешно удалена!")
#                 else:
#                     QMessageBox.warning(self, "Ошибка", "Ошибка при удалении точки")
    
#     def show_data_view(self):
#         # Полная сводка данных
#         points = self.db.get_points()
#         employees = self.db.get_employees()
#         products = self.db.get_products()
#         finances = self.db.get_finances()
#         supplies = self.db.get_supplies()
        
#         headers = ["Тип данных", "Количество записей"]
#         data = [
#             ["Точки", len(points)],
#             ["Сотрудники", len(employees)],
#             ["Продукты", len(products)],
#             ["Финансовые операции", len(finances)],
#             ["Поставки", len(supplies)]
#         ]
        
#         dialog = DataViewDialog("Сводка данных", headers, data, self)
#         dialog.exec()
    
#     def load_points(self):
#         try:
#             points = self.db.get_points()
#             self.points_table.setRowCount(len(points))
            
#             for row_idx, point in enumerate(points):
#                 for col_idx, value in enumerate(point):
#                     item = QTableWidgetItem(str(value) if value is not None else "")
#                     item.setFlags(item.flags() & ~Qt.ItemIsEditable)
#                     self.points_table.setItem(row_idx, col_idx, item)
            
#             self.points_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
#             print(f"Загружено точек: {len(points)}")
#         except Exception as e:
#             print(f"Ошибка загрузки точек: {e}")
    
#     def load_employees(self):
#         try:
#             employees = self.db.get_employees()
#             self.employees_table.setRowCount(len(employees))
            
#             for row_idx, emp in enumerate(employees):
#                 for col_idx, value in enumerate(emp[:6]):  # Берем только первые 6 колонок
#                     item = QTableWidgetItem(str(value) if value is not None else "")
#                     item.setFlags(item.flags() & ~Qt.ItemIsEditable)
#                     self.employees_table.setItem(row_idx, col_idx, item)
            
#             self.employees_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
#             print(f"Загружено сотрудников: {len(employees)}")
#         except Exception as e:
#             print(f"Ошибка загрузки сотрудников: {e}")
    
#     def load_products(self):
#         try:
#             products = self.db.get_products()
#             self.products_table.setRowCount(len(products))
            
#             for row_idx, product in enumerate(products):
#                 for col_idx, value in enumerate(product[:5]):  # Берем только первые 5 колонок
#                     item = QTableWidgetItem(str(value) if value is not None else "")
#                     item.setFlags(item.flags() & ~Qt.ItemIsEditable)
#                     self.products_table.setItem(row_idx, col_idx, item)
            
#             self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
#             print(f"Загружено продуктов: {len(products)}")
#         except Exception as e:
#             print(f"Ошибка загрузки продуктов: {e}")
    
#     def load_finances(self):
#         try:
#             finances = self.db.get_finances()
#             self.finances_table.setRowCount(len(finances))
            
#             for row_idx, finance in enumerate(finances):
#                 for col_idx, value in enumerate(finance):
#                     item = QTableWidgetItem(str(value) if value is not None else "")
#                     item.setFlags(item.flags() & ~Qt.ItemIsEditable)
#                     self.finances_table.setItem(row_idx, col_idx, item)
            
#             self.finances_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
#             print(f"Загружено финансовых операций: {len(finances)}")
#         except Exception as e:
#             print(f"Ошибка загрузки финансов: {e}")
    
#     def load_supplies(self):
#         try:
#             supplies = self.db.get_supplies()
#             self.supplies_table.setRowCount(len(supplies))
            
#             for row_idx, supply in enumerate(supplies):
#                 for col_idx, value in enumerate(supply):
#                     item = QTableWidgetItem(str(value) if value is not None else "")
#                     item.setFlags(item.flags() & ~Qt.ItemIsEditable)
#                     self.supplies_table.setItem(row_idx, col_idx, item)
            
#             self.supplies_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
#             print(f"Загружено поставок: {len(supplies)}")
#         except Exception as e:
#             print(f"Ошибка загрузки поставок: {e}")
    
#     def load_all_data(self):
#         """Загружает все данные во все таблицы"""
#         print("Начало загрузки всех данных...")
#         self.load_points()
#         self.load_employees()
#         self.load_products()
#         self.load_finances()
#         self.load_supplies()
#         print("Все данные загружены!")
    
#     def showEvent(self, event):
#         """Автоматически загружаем данные при показе окна"""
#         super().showEvent(event)
#         self.load_all_data()