from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QWidget, QGroupBox, QInputDialog, QCheckBox,
    QListWidget, QListWidgetItem, QSplitter, QFrame)
from PySide6.QtCore import Qt
import logging

class AlterTableDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Изменение структуры таблиц")
        self.setMinimumSize(700, 500)
        self.setup_ui()
        # В advanced_features.py в классе AlterTableDialog
    def execute_alter(self):
        sql = self.generate_sql()
        if not sql:
            QMessageBox.warning(self, "Ошибка", "Не удалось сгенерировать SQL запрос")
            return
            
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute(sql)
            self.db_manager.connection.commit()
            cursor.close()
            
            # ПОМЕЧАЕМ ЧТО СТРУКТУРА ИЗМЕНИЛАСЬ
            self.db_manager.mark_structure_changed()
            
            # ОБНОВЛЯЕМ СПИСКИ
            self.load_tables()
            self.load_columns()
            
            QMessageBox.information(self, "Успех", 
                "Структура таблицы успешно изменена!\n\n"
                "Чтобы увидеть изменения в окне просмотра данных:\n"
                "1. Закройте окно просмотра данных\n"
                "2. Откройте его заново\n"
                "3. Или нажмите 'Обновить структуру таблиц'")
            self.accept()
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Ошибка выполнения ALTER TABLE: {error_msg}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить операцию:\n{error_msg}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Выбор таблицы
        form_layout = QFormLayout()
        self.table_combo = QComboBox()
        self.load_tables()
        form_layout.addRow("Таблица:", self.table_combo)

        # Тип операции
        self.operation_combo = QComboBox()
        self.operation_combo.addItems([
            "Добавить столбец",
            "Удалить столбец", 
            "Переименовать таблицу",
            "Переименовать столбец",
            "Изменить тип данных",
            "Добавить ограничение",
            "Удалить ограничение"
        ])
        form_layout.addRow("Операция:", self.operation_combo)
        
        layout.addLayout(form_layout)

        # Динамическая форма для параметров
        self.params_widget = QWidget()
        self.params_layout = QFormLayout(self.params_widget)
        layout.addWidget(self.params_widget)

        self.operation_combo.currentTextChanged.connect(self.update_params_form)
        self.update_params_form()

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.execute_btn = QPushButton("Выполнить")
        self.preview_btn = QPushButton("Показать SQL")
        self.cancel_btn = QPushButton("Отмена")

        self.execute_btn.clicked.connect(self.execute_alter)
        self.preview_btn.clicked.connect(self.preview_sql)
        self.cancel_btn.clicked.connect(self.reject)

        buttons_layout.addWidget(self.execute_btn)
        buttons_layout.addWidget(self.preview_btn)
        buttons_layout.addWidget(self.cancel_btn)

        layout.addLayout(buttons_layout)

        # Поле для предпросмотра SQL
        self.sql_preview = QTextEdit()
        self.sql_preview.setReadOnly(True)
        self.sql_preview.setMaximumHeight(100)
        layout.addWidget(QLabel("SQL запрос:"))
        layout.addWidget(self.sql_preview)

        self.setLayout(layout)

    def load_tables(self):
        try:
            if self.db_manager.is_connected():
                cursor = self.db_manager.connection.cursor()
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                self.table_combo.clear()
                for table in tables:
                    self.table_combo.addItem(table[0])
                cursor.close()
        except Exception as e:
            logging.error(f"Ошибка загрузки таблиц: {str(e)}")

    def update_params_form(self):
        # Очищаем предыдущие поля
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)

        operation = self.operation_combo.currentText()
        
        if operation == "Добавить столбец":
            self.column_name_input = QLineEdit()
            self.data_type_combo = QComboBox()
            self.data_type_combo.addItems([
                "VARCHAR(255)", "INTEGER", "DECIMAL(10,2)", "DATE", 
                "BOOLEAN", "TEXT", "TIMESTAMP"
            ])
            self.nullable_check = QCheckBox("Разрешить NULL")
            self.nullable_check.setChecked(True)
            
            self.params_layout.addRow("Имя столбца:", self.column_name_input)
            self.params_layout.addRow("Тип данных:", self.data_type_combo)
            self.params_layout.addRow(self.nullable_check)
            
        elif operation == "Удалить столбец":
            self.column_combo = QComboBox()
            self.load_columns()
            self.params_layout.addRow("Столбец:", self.column_combo)
            
        elif operation == "Переименовать таблицу":
            self.new_table_name = QLineEdit()
            self.params_layout.addRow("Новое имя:", self.new_table_name)
            
        elif operation == "Переименовать столбец":
            self.old_column_combo = QComboBox()
            self.new_column_name = QLineEdit()
            self.load_columns()
            self.params_layout.addRow("Текущий столбец:", self.old_column_combo)
            self.params_layout.addRow("Новое имя:", self.new_column_name)
            
        elif operation == "Изменить тип данных":
            self.column_combo = QComboBox()
            self.new_data_type = QComboBox()
            self.new_data_type.addItems([
                "VARCHAR(255)", "INTEGER", "DECIMAL(10,2)", "DATE", 
                "BOOLEAN", "TEXT", "TIMESTAMP"
            ])
            self.load_columns()
            self.params_layout.addRow("Столбец:", self.column_combo)
            self.params_layout.addRow("Новый тип:", self.new_data_type)
            
        # В методе update_params_form класса AlterTableDialog
        elif operation == "Добавить ограничение":
            self.constraint_combo = QComboBox()
            self.constraint_combo.addItems(["NOT NULL", "UNIQUE", "CHECK", "FOREIGN KEY"])
            self.constraint_details = QLineEdit()
            
            # Добавляем подсказки для каждого типа ограничения
            self.constraint_combo.currentTextChanged.connect(self.update_constraint_hint)
            
            self.params_layout.addRow("Тип ограничения:", self.constraint_combo)
            self.params_layout.addRow("Детали:", self.constraint_details)
            
            self.hint_label = QLabel("")
            self.params_layout.addRow(self.hint_label)
            self.update_constraint_hint()

        
            self.hint_label.setText(hints.get(constraint_type, ""))
        elif operation == "Удалить ограничение":
            self.constraint_name = QLineEdit()
            self.params_layout.addRow("Имя ограничения:", self.constraint_name)
        def update_constraint_hint(self):
            constraint_type = self.constraint_combo.currentText()
            hints = {
                "NOT NULL": "Введите имя столбца (например: address)",
                "UNIQUE": "Введите имя столбца (например: phone_number)",
                "CHECK": "Введите условие (например: salary > 0)",
                "FOREIGN KEY": "Введите: column REFERENCES table(column) (например: point_id REFERENCES points(point_id))"
            }
    def execute_alter(self):
        sql = self.generate_sql()
        if not sql:
            QMessageBox.warning(self, "Ошибка", "Не удалось сгенерировать SQL запрос")
            return
            
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute(sql)
            self.db_manager.connection.commit()
            cursor.close()
            
            # ОБНОВЛЯЕМ СПИСКИ ТАБЛИЦ И СТОЛБЦОВ
            self.load_tables()
            self.load_columns()
            
            QMessageBox.information(self, "Успех", "Структура таблицы успешно изменена")
            self.accept()
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Ошибка выполнения ALTER TABLE: {error_msg}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить операцию:\n{error_msg}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
    def load_columns(self):
        try:
            table_name = self.table_combo.currentText()
            if table_name and self.db_manager.is_connected():
                cursor = self.db_manager.connection.cursor()
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = %s 
                    ORDER BY ordinal_position
                """, (table_name,))
                columns = cursor.fetchall()
                
                # Получаем текущий комбобокс (может быть разным в зависимости от операции)
                operation = self.operation_combo.currentText()
                if operation in ["Удалить столбец", "Переименовать столбец", "Изменить тип данных"]:
                    combo = getattr(self, 'column_combo', None) or getattr(self, 'old_column_combo', None)
                    if combo:
                        combo.clear()
                        for column in columns:
                            combo.addItem(column[0])
                cursor.close()
        except Exception as e:
            logging.error(f"Ошибка загрузки столбцов: {str(e)}")

    def generate_sql(self):
        operation = self.operation_combo.currentText()
        table_name = self.table_combo.currentText()
        
        if not table_name:
            return ""
            
        if operation == "Добавить столбец":
            column_name = self.column_name_input.text()
            data_type = self.data_type_combo.currentText()
            nullable = "NULL" if self.nullable_check.isChecked() else "NOT NULL"
            return f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type} {nullable}"
            
        elif operation == "Удалить столбец":
            column_name = self.column_combo.currentText()
            return f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
            
        elif operation == "Переименовать таблицу":
            new_name = self.new_table_name.text()
            return f"ALTER TABLE {table_name} RENAME TO {new_name}"
            
        elif operation == "Переименовать столбец":
            old_name = self.old_column_combo.currentText()
            new_name = self.new_column_name.text()
            return f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}"
            
        elif operation == "Изменить тип данных":
            column_name = self.column_combo.currentText()
            new_type = self.new_data_type.currentText()
            return f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {new_type}"
            
        elif operation == "Добавить ограничение":
            constraint_type = self.constraint_combo.currentText()
            details = self.constraint_details.text()
            
            if constraint_type == "NOT NULL":
                return f"ALTER TABLE {table_name} ALTER COLUMN {details} SET NOT NULL"
            elif constraint_type == "UNIQUE":
                return f"ALTER TABLE {table_name} ADD UNIQUE ({details})"
            elif constraint_type == "CHECK":
                return f"ALTER TABLE {table_name} ADD CHECK ({details})"
            elif constraint_type == "FOREIGN KEY":
                return f"ALTER TABLE {table_name} ADD FOREIGN KEY ({details})"
                
        elif operation == "Удалить ограничение":
            constraint_name = self.constraint_name.text()
            return f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}"
            
        return ""

    def preview_sql(self):
        sql = self.generate_sql()
        self.sql_preview.setPlainText(sql)

    def execute_alter(self):
        sql = self.generate_sql()
        if not sql:
            QMessageBox.warning(self, "Ошибка", "Не удалось сгенерировать SQL запрос")
            return
            
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute(sql)
            self.db_manager.connection.commit()
            cursor.close()
            
            QMessageBox.information(self, "Успех", "Структура таблицы успешно изменена")
            self.accept()
            
        except Exception as e:
            error_msg = str(e)
            logging.error(f"Ошибка выполнения ALTER TABLE: {error_msg}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось выполнить операцию:\n{error_msg}")
            if self.db_manager.connection:
                self.db_manager.connection.rollback()

class AdvancedSelectDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Расширенный SELECT")
        self.setMinimumSize(800, 600)
        self.setup_ui()

    def setup_ui(self):
            layout = QVBoxLayout()

            # Выбор таблицы
            top_layout = QHBoxLayout()
            self.table_combo = QComboBox()
            self.load_tables()
            top_layout.addWidget(QLabel("Таблица:"))
            top_layout.addWidget(self.table_combo)
            
            self.refresh_btn = QPushButton("Обновить")
            self.refresh_btn.clicked.connect(self.load_columns_list)
            top_layout.addWidget(self.refresh_btn)
            top_layout.addStretch()
            
            layout.addLayout(top_layout)

            splitter = QSplitter(Qt.Horizontal)
            
            # Левая панель - настройки запроса
            left_widget = QWidget()
            left_layout = QVBoxLayout(left_widget)
            
            # Выбор столбцов
            columns_group = QGroupBox("Выбор столбцов")
            columns_layout = QVBoxLayout()
            self.columns_list = QListWidget()
            self.columns_list.setSelectionMode(QListWidget.MultiSelection)
            columns_layout.addWidget(QLabel("Выберите столбцы для вывода:"))
            columns_layout.addWidget(self.columns_list)
            columns_group.setLayout(columns_layout)
            left_layout.addWidget(columns_group)

            # WHERE условия
            where_group = QGroupBox("Условия WHERE")
            where_layout = QFormLayout()
            self.where_column = QComboBox()
            self.where_operator = QComboBox()
            self.where_operator.addItems(["=", "!=", ">", "<", ">=", "<=", "LIKE", "IN", "IS NULL", "IS NOT NULL"])
            self.where_value = QLineEdit()
            self.where_value.setPlaceholderText("Для IS NULL/IS NOT NULL оставьте пустым")
            
            # Добавляем подсказки для операторов
            operator_hints = {
                "=": "Равно",
                "!=": "Не равно", 
                ">": "Больше",
                "<": "Меньше",
                ">=": "Больше или равно",
                "<=": "Меньше или равно",
                "LIKE": "Похоже на (используйте % для любых символов)",
                "IN": "В списке (например: value1,value2,value3)",
                "IS NULL": "Пустое значение",
                "IS NOT NULL": "Не пустое значение"
            }
            
            self.operator_hint_label = QLabel("")
            self.operator_hint_label.setWordWrap(True)
            self.operator_hint_label.setStyleSheet("color: #666; font-size: 9pt;")
            
            self.where_operator.currentTextChanged.connect(
                lambda text: self.operator_hint_label.setText(operator_hints.get(text, ""))
            )
            
            where_layout.addRow("Столбец:", self.where_column)
            where_layout.addRow("Оператор:", self.where_operator)
            where_layout.addRow("Значение:", self.where_value)
            where_layout.addRow(self.operator_hint_label)
            where_group.setLayout(where_layout)
            left_layout.addWidget(where_group)

            # GROUP BY и HAVING
            group_group = QGroupBox("Группировка")
            group_layout = QFormLayout()
            self.group_column = QComboBox()
            self.having_condition = QLineEdit()
            self.having_condition.setPlaceholderText("Например: COUNT(*) > 1")
            group_layout.addRow("GROUP BY столбец:", self.group_column)
            group_layout.addRow("HAVING условие:", self.having_condition)
            group_group.setLayout(group_layout)
            left_layout.addWidget(group_group)

            # ORDER BY
            order_group = QGroupBox("Сортировка")
            order_layout = QFormLayout()
            self.order_column = QComboBox()
            self.order_direction = QComboBox()
            self.order_direction.addItems(["ASC (по возрастанию)", "DESC (по убыванию)"])
            order_layout.addRow("Столбец:", self.order_column)
            order_layout.addRow("Направление:", self.order_direction)
            order_group.setLayout(order_layout)
            left_layout.addWidget(order_group)

            # Правая панель - результат
            right_widget = QWidget()
            right_layout = QVBoxLayout(right_widget)
            
            self.sql_preview = QTextEdit()
            self.sql_preview.setMaximumHeight(80)
            right_layout.addWidget(QLabel("SQL запрос:"))
            right_layout.addWidget(self.sql_preview)
            
            self.result_table = QTableWidget()
            right_layout.addWidget(self.result_table)

            splitter.addWidget(left_widget)
            splitter.addWidget(right_widget)
            splitter.setSizes([300, 500])
            layout.addWidget(splitter)

            # Кнопки выполнения
            buttons_layout = QHBoxLayout()
            self.execute_btn = QPushButton("Выполнить запрос")
            self.clear_btn = QPushButton("Очистить")
            self.close_btn = QPushButton("Закрыть")

            self.execute_btn.clicked.connect(self.execute_query)
            self.clear_btn.clicked.connect(self.clear_form)
            self.close_btn.clicked.connect(self.reject)

            buttons_layout.addWidget(self.execute_btn)
            buttons_layout.addWidget(self.clear_btn)
            buttons_layout.addWidget(self.close_btn)

            layout.addLayout(buttons_layout)
            self.setLayout(layout)

            self.table_combo.currentTextChanged.connect(self.load_columns_list)
            self.load_columns_list()

    def load_tables(self):
        try:
            if self.db_manager.is_connected():
                cursor = self.db_manager.connection.cursor()
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                self.table_combo.clear()
                for table in tables:
                    self.table_combo.addItem(table[0])
                cursor.close()
        except Exception as e:
            logging.error(f"Ошибка загрузки таблиц: {str(e)}")

    # В advanced_features.py в классе AdvancedSelectDialog
    def load_columns_list(self):
        table_name = self.table_combo.currentText()
        if not table_name:
            return
            
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cursor.fetchall()
            
            # ОЧИЩАЕМ И ЗАПОЛНЯЕМ ПРАВИЛЬНО
            self.columns_list.clear()
            self.where_column.clear()
            self.group_column.clear()
            self.order_column.clear()
            
            for column in columns:
                column_name = column[0]
                # Для списка с множественным выбором
                item = QListWidgetItem(column_name)
                self.columns_list.addItem(item)
                # Для комбобоксов
                self.where_column.addItem(column_name)
                self.group_column.addItem(column_name)
                self.order_column.addItem(column_name)
                
            cursor.close()
            self.update_sql_preview()
            
        except Exception as e:
            logging.error(f"Ошибка загрузки столбцов: {str(e)}")

    def update_sql_preview(self):
        sql = self.generate_sql()
        self.sql_preview.setPlainText(sql)

    def generate_sql(self):
        table_name = self.table_combo.currentText()
        if not table_name:
            return ""
            
        # SELECT часть
        selected_columns = [item.text() for item in self.columns_list.selectedItems()]
        columns = ", ".join(selected_columns) if selected_columns else "*"
        
        sql = f"SELECT {columns} FROM {table_name}"
        
        # WHERE часть
        where_col = self.where_column.currentText()
        where_op = self.where_operator.currentText()
        where_val = self.where_value.text().strip()
        
        if where_col and where_op:
            if where_op in ["IS NULL", "IS NOT NULL"]:
                sql += f" WHERE {where_col} {where_op}"
            elif where_col and where_val:
                if where_op == "IN":
                    # Форматируем значения для IN
                    values = ",".join([f"'{v.strip()}'" for v in where_val.split(",")])
                    sql += f" WHERE {where_col} {where_op} ({values})"
                elif where_op == "LIKE":
                    sql += f" WHERE {where_col} {where_op} '%{where_val}%'"
                else:
                    sql += f" WHERE {where_col} {where_op} '{where_val}'"
                    
        # GROUP BY часть
        group_col = self.group_column.currentText()
        if group_col:
            sql += f" GROUP BY {group_col}"
            
        # HAVING часть
        having_cond = self.having_condition.text()
        if having_cond and group_col:
            sql += f" HAVING {having_cond}"
            
        # ORDER BY часть
        order_col = self.order_column.currentText()
        if order_col:
            order_dir = "ASC" if "ASC" in self.order_direction.currentText() else "DESC"
            sql += f" ORDER BY {order_col} {order_dir}"
            
        return sql

    def execute_query(self):
        sql = self.generate_sql()
        if not sql:
            return
            
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            
            # Получаем описание столбцов
            columns = [desc[0] for desc in cursor.description]
            
            # Заполняем таблицу
            self.result_table.setRowCount(len(result))
            self.result_table.setColumnCount(len(columns))
            self.result_table.setHorizontalHeaderLabels(columns)
            
            for row_idx, row_data in enumerate(result):
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    self.result_table.setItem(row_idx, col_idx, item)
                    
            cursor.close()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка выполнения запроса:\n{str(e)}")

    def clear_form(self):
        self.columns_list.clearSelection()
        self.where_column.setCurrentIndex(0)
        self.where_operator.setCurrentIndex(0)
        self.where_value.clear()
        self.group_column.setCurrentIndex(0)
        self.having_condition.clear()
        self.order_column.setCurrentIndex(0)
        self.order_direction.setCurrentIndex(0)
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.sql_preview.clear()

class TextSearchDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Поиск по тексту")
        self.setMinimumSize(600, 400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Выбор таблицы и столбца
        form_layout = QFormLayout()
        self.table_combo = QComboBox()
        self.column_combo = QComboBox()
        self.load_tables()
        
        form_layout.addRow("Таблица:", self.table_combo)
        form_layout.addRow("Столбец:", self.column_combo)
        layout.addLayout(form_layout)

        # Тип поиска
        search_layout = QHBoxLayout()
        self.search_type = QComboBox()
        self.search_type.addItems(["LIKE", "POSIX - базовый", "POSIX - расширенный"])
        
        self.search_pattern = QLineEdit()
        self.search_pattern.setPlaceholderText("Введите шаблон для поиска")
        
        search_layout.addWidget(QLabel("Тип поиска:"))
        search_layout.addWidget(self.search_type)
        search_layout.addWidget(QLabel("Шаблон:"))
        search_layout.addWidget(self.search_pattern)
        layout.addLayout(search_layout)

        # Пояснения для типов поиска
        self.search_hint = QLabel()
        self.search_hint.setWordWrap(True)
        self.search_hint.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        layout.addWidget(self.search_hint)

        # Обновляем подсказки при изменении типа поиска
        self.search_type.currentTextChanged.connect(self.update_search_hint)
        self.update_search_hint()

        # Кнопки поиска
        buttons_layout = QHBoxLayout()
        self.search_btn = QPushButton("Найти")
        self.clear_btn = QPushButton("Очистить")
        
        self.search_btn.clicked.connect(self.execute_search)
        self.clear_btn.clicked.connect(self.clear_results)
        
        buttons_layout.addWidget(self.search_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Результаты
        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)

        self.setLayout(layout)
        
        self.table_combo.currentTextChanged.connect(self.load_columns)
        self.load_columns()

    def update_search_hint(self):
        search_type = self.search_type.currentText()
        hints = {
            "LIKE": "Используйте % для любых символов и _ для одного символа. Пример: 'Ива%' найдет 'Иванов'",
            "POSIX - базовый": "Базовые регулярные выражения. Пример: '^Иван' найдет строки, начинающиеся с 'Иван'",
            "POSIX - расширенный": "Расширенные регулярные выражения (регистронезависимые). Пример: 'петр|иван' найдет 'Петр' или 'Иван'"
        }
        self.search_hint.setText(hints.get(search_type, ""))

    def load_tables(self):
        try:
            if self.db_manager.is_connected():
                cursor = self.db_manager.connection.cursor()
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                self.table_combo.clear()
                for table in tables:
                    self.table_combo.addItem(table[0])
                cursor.close()
        except Exception as e:
            logging.error(f"Ошибка загрузки таблиц: {str(e)}")

    def load_columns(self):
        table_name = self.table_combo.currentText()
        if not table_name:
            return
            
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cursor.fetchall()
            
            self.column_combo.clear()
            for column in columns:
                # Показываем только текстовые столбцы для поиска
                if column[1] in ['character varying', 'text', 'char']:
                    self.column_combo.addItem(column[0])
                    
            cursor.close()
            
        except Exception as e:
            logging.error(f"Ошибка загрузки столбцов: {str(e)}")

    def execute_search(self):
        table_name = self.table_combo.currentText()
        column_name = self.column_combo.currentText()
        pattern = self.search_pattern.text()
        search_type = self.search_type.currentText()
        
        if not all([table_name, column_name, pattern]):
            QMessageBox.warning(self, "Ошибка", "Заполните все поля")
            return
            
        try:
            cursor = self.db_manager.connection.cursor()
            
            if search_type == "LIKE":
                sql = f"SELECT * FROM {table_name} WHERE {column_name} LIKE %s"
                cursor.execute(sql, (f"%{pattern}%",))
            elif search_type == "POSIX - базовый":
                sql = f"SELECT * FROM {table_name} WHERE {column_name} ~ %s"
                cursor.execute(sql, (pattern,))
            elif search_type == "POSIX - расширенный":
                sql = f"SELECT * FROM {table_name} WHERE {column_name} ~* %s"
                cursor.execute(sql, (pattern,))
                
            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]
            
            # Заполняем таблицу
            self.result_table.setRowCount(len(result))
            self.result_table.setColumnCount(len(columns))
            self.result_table.setHorizontalHeaderLabels(columns)
            
            for row_idx, row_data in enumerate(result):
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    self.result_table.setItem(row_idx, col_idx, item)
                    
            cursor.close()
            
            if len(result) == 0:
                QMessageBox.information(self, "Результат", "Ничего не найдено")
                
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка поиска:\n{str(e)}")

    def clear_results(self):
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.search_pattern.clear()

class StringFunctionsDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Функции работы со строками")
        self.setMinimumSize(700, 500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Выбор таблицы и столбца
        form_layout = QFormLayout()
        self.table_combo = QComboBox()
        self.column_combo = QComboBox()
        self.load_tables()
        
        form_layout.addRow("Таблица:", self.table_combo)
        form_layout.addRow("Текстовый столбец:", self.column_combo)
        layout.addLayout(form_layout)

        # Выбор функции
        functions_group = QGroupBox("Функции работы со строками")
        functions_layout = QVBoxLayout()
        
        self.function_combo = QComboBox()
        self.function_combo.addItems([
            "UPPER - в верхний регистр",
            "LOWER - в нижний регистр", 
            "SUBSTRING - извлечь подстроку",
            "TRIM - удалить пробелы",
            "LTRIM - удалить пробелы слева",
            "RTRIM - удалить пробелы справа",
            "LPAD - дополнить слева",
            "RPAD - дополнить справа",
            "CONCAT - объединить строки",
            "LENGTH - длина строки"
        ])
        
        functions_layout.addWidget(QLabel("Функция:"))
        functions_layout.addWidget(self.function_combo)
        
        # Параметры для функций
        self.params_widget = QWidget()
        self.params_layout = QFormLayout(self.params_widget)
        functions_layout.addWidget(self.params_widget)
        
        functions_group.setLayout(functions_layout)
        layout.addWidget(functions_group)

        self.function_combo.currentTextChanged.connect(self.update_params)
        self.update_params()

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.apply_btn = QPushButton("Применить к данным")
        self.preview_btn = QPushButton("Показать пример")
        
        self.apply_btn.clicked.connect(self.apply_to_data)
        self.preview_btn.clicked.connect(self.show_example)
        
        buttons_layout.addWidget(self.apply_btn)
        buttons_layout.addWidget(self.preview_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # Результаты
        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)

        self.setLayout(layout)
        
        self.table_combo.currentTextChanged.connect(self.load_columns)
        self.load_columns()

    def load_tables(self):
        try:
            if self.db_manager.is_connected():
                cursor = self.db_manager.connection.cursor()
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                self.table_combo.clear()
                for table in tables:
                    self.table_combo.addItem(table[0])
                cursor.close()
        except Exception as e:
            logging.error(f"Ошибка загрузки таблиц: {str(e)}")

    def load_columns(self):
        table_name = self.table_combo.currentText()
        if not table_name:
            return
            
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cursor.fetchall()
            
            self.column_combo.clear()
            for column in columns:
                # Показываем только текстовые столбцы
                if column[1] in ['character varying', 'text', 'char']:
                    self.column_combo.addItem(column[0])
                    
            cursor.close()
            
        except Exception as e:
            logging.error(f"Ошибка загрузки столбцов: {str(e)}")

    def update_params(self):
        # Очищаем предыдущие поля
        while self.params_layout.rowCount() > 0:
            self.params_layout.removeRow(0)

        function = self.function_combo.currentText()
        
        if "SUBSTRING" in function:
            self.start_input = QLineEdit()
            self.length_input = QLineEdit()
            self.params_layout.addRow("Начальная позиция:", self.start_input)
            self.params_layout.addRow("Длина:", self.length_input)
            
        elif "LPAD" in function or "RPAD" in function:
            self.length_input = QLineEdit()
            self.pad_char = QLineEdit()
            self.pad_char.setText(" ")
            self.params_layout.addRow("Длина:", self.length_input)
            self.params_layout.addRow("Символ:", self.pad_char)
            
        elif "CONCAT" in function:
            self.concat_text = QLineEdit()
            self.params_layout.addRow("Текст для объединения:", self.concat_text)

    def get_function_sql(self):
        function = self.function_combo.currentText()
        column = self.column_combo.currentText()
        
        if "UPPER" in function:
            return f"UPPER({column})"
        elif "LOWER" in function:
            return f"LOWER({column})"
        elif "SUBSTRING" in function:
            start = self.start_input.text() or "1"
            length = self.length_input.text() or "10"
            return f"SUBSTRING({column} FROM {start} FOR {length})"
        elif "TRIM" in function:
            return f"TRIM({column})"
        elif "LTRIM" in function:
            return f"LTRIM({column})"
        elif "RTRIM" in function:
            return f"RTRIM({column})"
        elif "LPAD" in function:
            length = self.length_input.text() or "10"
            pad_char = self.pad_char.text() or " "
            return f"LPAD({column}, {length}, '{pad_char}')"
        elif "RPAD" in function:
            length = self.length_input.text() or "10"
            pad_char = self.pad_char.text() or " "
            return f"RPAD({column}, {length}, '{pad_char}')"
        elif "CONCAT" in function:
            concat_text = self.concat_text.text() or ""
            return f"CONCAT({column}, '{concat_text}')"
        elif "LENGTH" in function:
            return f"LENGTH({column})"
            
        return column

    def apply_to_data(self):
        table_name = self.table_combo.currentText()
        column = self.column_combo.currentText()
        
        if not all([table_name, column]):
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу и столбец")
            return
            
        try:
            function_sql = self.get_function_sql()
            cursor = self.db_manager.connection.cursor()
            
            # ВАЖНО: используем правильное имя столбца в SQL
            sql = f"SELECT {column} as original, {function_sql} as result FROM {table_name} LIMIT 50"
            cursor.execute(sql)
            result = cursor.fetchall()
            
            # Заполняем таблицу
            self.result_table.setRowCount(len(result))
            self.result_table.setColumnCount(2)
            self.result_table.setHorizontalHeaderLabels(["Исходное значение", "Результат"])
            
            for row_idx, row_data in enumerate(result):
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    self.result_table.setItem(row_idx, col_idx, item)
                    
            cursor.close()
            
        except Exception as e:
            # ВАЖНО: не оставляем "висячих" транзакций
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            QMessageBox.warning(self, "Ошибка", f"Ошибка применения функции:\n{str(e)}")

    def show_example(self):
        function_sql = self.get_function_sql()
        example_text = "Пример текста"
        
        try:
            cursor = self.db_manager.connection.cursor()
            sql = f"SELECT '{example_text}' AS original, {function_sql.replace('column', '\"Пример текста\"')} AS result"
            cursor.execute(sql)
            result = cursor.fetchone()
            
            QMessageBox.information(self, "Пример", 
                f"Исходный текст: '{example_text}'\n"
                f"Результат: '{result[1]}'")
                
            cursor.close()
            
        except Exception as e:
            QMessageBox.warning(self, "Ошибка", f"Ошибка демонстрации:\n{str(e)}")

class JoinWizardDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Мастер соединений JOIN")
        self.setMinimumSize(900, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Настройки JOIN
        join_layout = QHBoxLayout()
        
        # Левая таблица
        left_group = QGroupBox("Левая таблица")
        left_layout = QVBoxLayout()
        self.left_table = QComboBox()
        self.left_column = QComboBox()
        left_layout.addWidget(QLabel("Таблица:"))
        left_layout.addWidget(self.left_table)
        left_layout.addWidget(QLabel("Столбец:"))
        left_layout.addWidget(self.left_column)
        left_group.setLayout(left_layout)
        join_layout.addWidget(left_group)

        # Тип JOIN
        center_group = QGroupBox("Тип соединения")
        center_layout = QVBoxLayout()
        self.join_type = QComboBox()
        self.join_type.addItems([
            "INNER JOIN",
            "LEFT JOIN", 
            "RIGHT JOIN",
            "FULL JOIN"
        ])
        center_layout.addWidget(self.join_type)
        center_group.setLayout(center_layout)
        join_layout.addWidget(center_group)

        # Правая таблица
        right_group = QGroupBox("Правая таблица")
        right_layout = QVBoxLayout()
        self.right_table = QComboBox()
        self.right_column = QComboBox()
        right_layout.addWidget(QLabel("Таблица:"))
        right_layout.addWidget(self.right_table)
        right_layout.addWidget(QLabel("Столбец:"))
        right_layout.addWidget(self.right_column)
        right_group.setLayout(right_layout)
        join_layout.addWidget(right_group)

        layout.addLayout(join_layout)

        # Выбор столбцов для вывода
        columns_group = QGroupBox("Столбцы для вывода")
        columns_layout = QHBoxLayout()
        
        self.left_columns = QListWidget()
        self.left_columns.setSelectionMode(QListWidget.MultiSelection)
        self.right_columns = QListWidget()
        self.right_columns.setSelectionMode(QListWidget.MultiSelection)
        
        columns_layout.addWidget(QLabel("Левая таблица:"))
        columns_layout.addWidget(self.left_columns)
        columns_layout.addWidget(QLabel("Правая таблица:"))
        columns_layout.addWidget(self.right_columns)
        
        columns_group.setLayout(columns_layout)
        layout.addWidget(columns_group)

        # Кнопки
        buttons_layout = QHBoxLayout()
        self.execute_btn = QPushButton("Выполнить JOIN")
        self.clear_btn = QPushButton("Очистить")
        
        self.execute_btn.clicked.connect(self.execute_join)
        self.clear_btn.clicked.connect(self.clear_results)
        
        buttons_layout.addWidget(self.execute_btn)
        buttons_layout.addWidget(self.clear_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        # SQL предпросмотр
        self.sql_preview = QTextEdit()
        self.sql_preview.setMaximumHeight(80)
        layout.addWidget(QLabel("SQL запрос:"))
        layout.addWidget(self.sql_preview)

        # Результаты
        self.result_table = QTableWidget()
        layout.addWidget(self.result_table)

        self.setLayout(layout)
        
        # Подключаем сигналы
        self.left_table.currentTextChanged.connect(self.on_left_table_changed)
        self.right_table.currentTextChanged.connect(self.on_right_table_changed)
        self.left_table.currentTextChanged.connect(self.update_sql_preview)
        self.right_table.currentTextChanged.connect(self.update_sql_preview)
        self.left_column.currentTextChanged.connect(self.update_sql_preview)
        self.right_column.currentTextChanged.connect(self.update_sql_preview)
        self.join_type.currentTextChanged.connect(self.update_sql_preview)
        
        self.load_tables()

    def load_tables(self):
        try:
            if self.db_manager.is_connected():
                cursor = self.db_manager.connection.cursor()
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
                tables = cursor.fetchall()
                
                for combo in [self.left_table, self.right_table]:
                    combo.clear()
                    for table in tables:
                        combo.addItem(table[0])
                        
                cursor.close()
        except Exception as e:
            logging.error(f"Ошибка загрузки таблиц: {str(e)}")

    def on_left_table_changed(self):
        table_name = self.left_table.currentText()
        if table_name:
            self.load_table_columns(table_name, self.left_column, self.left_columns)

    def on_right_table_changed(self):
        table_name = self.right_table.currentText()
        if table_name:
            self.load_table_columns(table_name, self.right_column, self.right_columns)

    def load_table_columns(self, table_name, column_combo, columns_list):
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = %s 
                ORDER BY ordinal_position
            """, (table_name,))
            columns = cursor.fetchall()
            
            column_combo.clear()
            columns_list.clear()
            
            for column in columns:
                column_combo.addItem(column[0])
                columns_list.addItem(column[0])
                
            cursor.close()
            
        except Exception as e:
            logging.error(f"Ошибка загрузки столбцов: {str(e)}")

    def update_sql_preview(self):
        sql = self.generate_sql()
        self.sql_preview.setPlainText(sql)

    def generate_sql(self):
        operation = self.operation_combo.currentText()
        table_name = self.table_combo.currentText()
        
        if not table_name:
            return ""
            
        if operation == "Добавить столбец":
            column_name = self.column_name_input.text()
            data_type = self.data_type_combo.currentText()
            nullable = "NULL" if self.nullable_check.isChecked() else "NOT NULL"
            return f"ALTER TABLE {table_name} ADD COLUMN {column_name} {data_type} {nullable}"
            
        elif operation == "Удалить столбец":
            column_name = self.column_combo.currentText()
            return f"ALTER TABLE {table_name} DROP COLUMN {column_name}"
            
        elif operation == "Переименовать таблицу":
            new_name = self.new_table_name.text()
            return f"ALTER TABLE {table_name} RENAME TO {new_name}"
            
        elif operation == "Переименовать столбец":
            old_name = self.old_column_combo.currentText()
            new_name = self.new_column_name.text()
            return f"ALTER TABLE {table_name} RENAME COLUMN {old_name} TO {new_name}"
            
        elif operation == "Изменить тип данных":
            column_name = self.column_combo.currentText()
            new_type = self.new_data_type.currentText()
            return f"ALTER TABLE {table_name} ALTER COLUMN {column_name} TYPE {new_type}"
            
        elif operation == "Добавить ограничение":
            constraint_type = self.constraint_combo.currentText()
            details = self.constraint_details.text().strip()
            
            if constraint_type == "NOT NULL":
                # ИСПРАВЛЕННЫЙ СИНТАКСИС
                return f"ALTER TABLE {table_name} ALTER COLUMN {details} SET NOT NULL"
            elif constraint_type == "UNIQUE":
                return f"ALTER TABLE {table_name} ADD CONSTRAINT {table_name}_{details}_unique UNIQUE ({details})"
            elif constraint_type == "CHECK":
                return f"ALTER TABLE {table_name} ADD CONSTRAINT {table_name}_check CHECK ({details})"
            elif constraint_type == "FOREIGN KEY":
                # Ожидается формат: column REFERENCES table(column)
                parts = details.split()
                if len(parts) >= 4 and parts[1].upper() == "REFERENCES":
                    column = parts[0]
                    ref_table = parts[2].split('(')[0]
                    return f"ALTER TABLE {table_name} ADD FOREIGN KEY ({column}) REFERENCES {ref_table}({parts[2].split('(')[1].rstrip(')')})"
                else:
                    return f"ALTER TABLE {table_name} ADD FOREIGN KEY ({details})"
                    
        elif operation == "Удалить ограничение":
            constraint_name = self.constraint_name.text()
            return f"ALTER TABLE {table_name} DROP CONSTRAINT {constraint_name}"
            
        return ""

  # В advanced_features.py в классе JoinWizardDialog
    def execute_join(self):
        sql = self.generate_sql()
        if not sql:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицы и столбцы для соединения")
            return
            
        try:
            cursor = self.db_manager.connection.cursor()
            cursor.execute(sql)
            result = cursor.fetchall()
            
            columns = [desc[0] for desc in cursor.description]
            
            # Заполняем таблицу
            self.result_table.setRowCount(len(result))
            self.result_table.setColumnCount(len(columns))
            self.result_table.setHorizontalHeaderLabels(columns)
            
            for row_idx, row_data in enumerate(result):
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    self.result_table.setItem(row_idx, col_idx, item)
                    
            cursor.close()
            
            QMessageBox.information(self, "Успех", f"Найдено {len(result)} записей")
            
        except Exception as e:
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            QMessageBox.warning(self, "Ошибка", f"Ошибка выполнения JOIN:\n{str(e)}")

    def clear_results(self):
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.sql_preview.clear()