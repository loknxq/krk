from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QWidget, QGroupBox, QInputDialog, QCheckBox,
    QListWidget, QListWidgetItem, QSplitter, QFrame)
from PySide6.QtCore import Qt
import logging


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

        search_layout = QHBoxLayout()
        self.search_type = QComboBox()
        self.search_type.addItems([
            "LIKE",
            "NOT LIKE",
            "POSIX - базовый",
            "POSIX - расширенный",
            "SIMILAR TO",
            "NOT SIMILAR TO"
        ])

        self.search_pattern = QLineEdit()
        self.search_pattern.setPlaceholderText("Введите шаблон для поиска")

        search_layout.addWidget(QLabel("Тип поиска:"))
        search_layout.addWidget(self.search_type)
        search_layout.addWidget(QLabel("Шаблон:"))
        search_layout.addWidget(self.search_pattern)
        layout.addLayout(search_layout)

        self.search_hint = QLabel()
        self.search_hint.setWordWrap(True)
        self.search_hint.setStyleSheet("color: #666; font-size: 9pt; padding: 5px;")
        layout.addWidget(self.search_hint)

        self.search_type.currentTextChanged.connect(self.update_search_hint)
        self.update_search_hint()

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
            "LIKE":
                "Используйте % для любых символов и _ для одного символа.\n"
                "Пример: 'Ива%' найдет 'Иванов', 'Иван'",

            "NOT LIKE":
                "Находит строки, которые НЕ соответствуют шаблону.\n"
                "Пример: 'Ива%' исключит 'Иванов', 'Иван'",

            "POSIX - базовый":
                "Базовые регулярные выражения. Чувствительны к регистру.\n"
                "Пример: '^Иван' найдет строки, начинающиеся с 'Иван'",

            "POSIX - расширенный":
                "Расширенные регулярные выражения (регистронезависимые).\n"
                "Пример: 'петр|иван' найдет 'Петр' или 'Иван'",

            "SIMILAR TO":
                "Пример: '(Иван|Петр)%' найдет строки, начинающиеся с 'Иван' или 'Петр'\n"
                "Синтаксис: % - любая строка, _ - один символ, | - ИЛИ, * - повторение 0+ раз, + - повторение 1+ раз",

            "NOT SIMILAR TO":
                "Находит строки, которые не соответствуют шаблону SIMILAR TO.\n"
                "Пример: '(Иван|Петр)%' исключит строки, начинающиеся с 'Иван' или 'Петр'"
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
            elif search_type == "NOT LIKE":
                sql = f"SELECT * FROM {table_name} WHERE {column_name} NOT LIKE %s"
                cursor.execute(sql, (f"%{pattern}%",))
            elif search_type == "POSIX - базовый":
                sql = f"SELECT * FROM {table_name} WHERE {column_name} ~ %s"
                cursor.execute(sql, (pattern,))
            elif search_type == "POSIX - расширенный":
                sql = f"SELECT * FROM {table_name} WHERE {column_name} ~* %s"
                cursor.execute(sql, (pattern,))
            elif search_type == "SIMILAR TO":
                sql = f"SELECT * FROM {table_name} WHERE {column_name} SIMILAR TO %s"
                cursor.execute(sql, (pattern,))
            elif search_type == "NOT SIMILAR TO":
                sql = f"SELECT * FROM {table_name} WHERE {column_name} NOT SIMILAR TO %s"
                cursor.execute(sql, (pattern,))

            result = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

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

        form_layout = QFormLayout()
        self.table_combo = QComboBox()
        self.column_combo = QComboBox()
        self.load_tables()

        form_layout.addRow("Таблица:", self.table_combo)
        form_layout.addRow("Текстовый столбец:", self.column_combo)
        layout.addLayout(form_layout)

        # Выбор функции
        functions_group = QGroupBox("Функции для обновления данных")
        functions_layout = QVBoxLayout()

        self.function_combo = QComboBox()
        self.function_combo.addItems([
            "UPPER - преобразовать в верхний регистр",
            "LOWER - преобразовать в нижний регистр",
            "SUBSTRING - извлечь подстроку",
            "TRIM - удалить пробелы с обеих сторон",
            "LTRIM - удалить пробелы слева",
            "RTRIM - удалить пробелы справа",
            "LPAD - дополнить строку слева",
            "RPAD - дополнить строку справа",
            "CONCAT - объединить с другой строкой"
        ])

        functions_layout.addWidget(QLabel("Функция преобразования:"))
        functions_layout.addWidget(self.function_combo)

        self.params_widget = QWidget()
        self.params_layout = QFormLayout(self.params_widget)
        functions_layout.addWidget(self.params_widget)

        functions_group.setLayout(functions_layout)
        layout.addWidget(functions_group)

        self.function_combo.currentTextChanged.connect(self.update_params)
        self.update_params()

        buttons_layout = QHBoxLayout()
        self.preview_btn = QPushButton("Предварительный просмотр")
        self.update_btn = QPushButton("Выполнить обновление")

        self.preview_btn.clicked.connect(self.preview_changes)
        self.update_btn.clicked.connect(self.execute_update)

        buttons_layout.addWidget(self.preview_btn)
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)

        preview_group = QGroupBox("Предварительный просмотр изменений")
        preview_layout = QVBoxLayout()
        self.preview_table = QTableWidget()
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Статус выполнения
        self.status_label = QLabel("Выберите таблицу, столбец и функцию")
        layout.addWidget(self.status_label)

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
            self.start_input.setPlaceholderText("1")
            self.length_input = QLineEdit()
            self.length_input.setPlaceholderText("10")
            self.params_layout.addRow("Начальная позиция (от 1):", self.start_input)
            self.params_layout.addRow("Длина подстроки:", self.length_input)

        elif "LPAD" in function or "RPAD" in function:
            self.length_input = QLineEdit()
            self.length_input.setPlaceholderText("10")
            self.pad_char = QLineEdit()
            self.pad_char.setText(" ")
            self.pad_char.setMaxLength(1)
            self.params_layout.addRow("Желаемая длина строки:", self.length_input)
            self.params_layout.addRow("Символ заполнения:", self.pad_char)

        elif "CONCAT" in function:
            self.concat_text = QLineEdit()
            self.concat_text.setPlaceholderText("Введите текст для добавления")
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

        return column

    def preview_changes(self):
        table_name = self.table_combo.currentText()
        column = self.column_combo.currentText()

        if not all([table_name, column]):
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу и столбец")
            return

        try:
            function_sql = self.get_function_sql()
            cursor = self.db_manager.connection.cursor()

            sql = f"""
                SELECT 
                    {column} as original, 
                    {function_sql} as new_value 
                FROM {table_name} 
                WHERE {column} IS NOT NULL 
                LIMIT 10
            """
            cursor.execute(sql)
            result = cursor.fetchall()

            self.preview_table.setRowCount(len(result))
            self.preview_table.setColumnCount(2)
            self.preview_table.setHorizontalHeaderLabels(["Текущее значение", "Будет изменено на"])

            for row_idx, row_data in enumerate(result):
                for col_idx, cell_data in enumerate(row_data):
                    item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                    self.preview_table.setItem(row_idx, col_idx, item)

            cursor.close()

            cursor = self.db_manager.connection.cursor()
            count_sql = f"SELECT COUNT(*) FROM {table_name} WHERE {column} IS NOT NULL"
            cursor.execute(count_sql)
            total_count = cursor.fetchone()[0]
            cursor.close()

            self.status_label.setText(
                f"Будет обновлено строк: {total_count}. Посмотрите предварительный просмотр выше.")

        except Exception as e:
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            QMessageBox.warning(self, "Ошибка", f"Ошибка предварительного просмотра:\n{str(e)}")

    def execute_update(self):
        table_name = self.table_combo.currentText()
        column = self.column_combo.currentText()

        if not all([table_name, column]):
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу и столбец")
            return

        reply = QMessageBox.question(
            self,
            "Подтверждение обновления",
            f"Вы уверены, что хотите обновить данные в таблице '{table_name}'?\n\n"
            f"Столбец '{column}' будет обновлен для всех строк.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply != QMessageBox.Yes:
            return

        try:
            function_sql = self.get_function_sql()
            cursor = self.db_manager.connection.cursor()

            update_sql = f"UPDATE {table_name} SET {column} = {function_sql} WHERE {column} IS NOT NULL"
            cursor.execute(update_sql)
            updated_count = cursor.rowcount

            self.db_manager.connection.commit()

            cursor.close()

            QMessageBox.information(
                self,
                "Обновление завершено",
                f"Успешно обновлено строк: {updated_count}\n\n"
                f"Таблица: {table_name}\n"
                f"Столбец: {column}\n"
                f"Операция: {self.function_combo.currentText()}"
            )

            self.status_label.setText(f"Обновлено строк: {updated_count}")

            self.preview_table.setRowCount(0)

        except Exception as e:
            if self.db_manager.connection:
                self.db_manager.connection.rollback()
            QMessageBox.warning(
                self,
                "Ошибка обновления",
                f"Не удалось обновить данные:\n{str(e)}"
            )
            self.status_label.setText("Ошибка при обновлении данных")