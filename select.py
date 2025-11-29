import re
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QWidget, QGroupBox, QInputDialog, QCheckBox,
    QListWidget, QListWidgetItem, QSplitter, QFrame, QScrollArea,
    QSpinBox
)
from PySide6.QtCore import Qt, Signal


class JoinDialog(QDialog):
    def __init__(self, schema, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добавить соединение")
        self.schema = schema or {}
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        self.left_table_cb = QComboBox()
        self.left_table_cb.addItems(sorted(self.schema.keys()))
        self.right_table_cb = QComboBox()
        self.right_table_cb.addItems(sorted(self.schema.keys()))
        self.left_field_cb = QComboBox()
        self.right_field_cb = QComboBox()
        self.update_fields()
        self.left_table_cb.currentIndexChanged.connect(self.update_fields)
        self.right_table_cb.currentIndexChanged.connect(self.update_fields)
        self.join_type_cb = QComboBox()
        self.join_type_cb.addItems(['INNER', 'LEFT', 'RIGHT', 'FULL'])
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.accept)
        layout.addRow('Левая таблица', self.left_table_cb)
        layout.addRow('Правая таблица', self.right_table_cb)
        layout.addRow('Поле (слева)', self.left_field_cb)
        layout.addRow('Поле (справа)', self.right_field_cb)
        layout.addRow('Тип', self.join_type_cb)
        layout.addRow(add_btn)

    def update_fields(self):
        lt = self.left_table_cb.currentText()
        rt = self.right_table_cb.currentText()
        self.left_field_cb.clear()
        self.right_field_cb.clear()
        if lt and lt in self.schema:
            self.left_field_cb.addItems(self.schema.get(lt, []))
        if rt and rt in self.schema:
            self.right_field_cb.addItems(self.schema.get(rt, []))

    def get_join(self):
        left = self.left_table_cb.currentText()
        right = self.right_table_cb.currentText()
        lf = self.left_field_cb.currentText()
        rf = self.right_field_cb.currentText()
        jtype = self.join_type_cb.currentText()
        desc = f"{jtype} JOIN {right} ON {left}.{lf} = {right}.{rf}"
        return {
            'type': jtype,
            'left': left,
            'right': right,
            'lf': lf,
            'rf': rf,
            'desc': desc
        }


class SubqueryDialog(QDialog):
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Составить подзапрос')
        self.result_sql = ''
        self.db = db
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        # многострочное поле для SQL
        self.sql_widget = QTextEdit()
        layout.addWidget(QLabel("Введите SQL подзапрос (SELECT ...):"))
        layout.addWidget(self.sql_widget)

        btn_row = QHBoxLayout()
        # Кнопка для открытия встроенного билдера (еще один экземпляр главного окна)
        self.compose_btn = QPushButton('Составить подзапрос')
        self.compose_btn.clicked.connect(self.open_sub_builder)
        add_btn = QPushButton('Добавить')
        cancel_btn = QPushButton('Отмена')
        add_btn.clicked.connect(self.on_add)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(self.compose_btn)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

    def open_sub_builder(self):
        # Открываем полную форму билдера для составления подзапроса
        if not self.db:
            QMessageBox.warning(self, 'Нет DB', 'DBManager не передан — невозможно открыть билдер.')
            return
        builder = AdvancedSelectDialog(self.db, parent=self)

        # при emit переносим sql в поле сразу
        def on_apply_sql(sql):
            if sql:
                self.sql_widget.setPlainText(sql)

        builder.apply_sql.connect(on_apply_sql)
        # открываем модально; после закрытия проверим финальный финтекст
        builder.exec()
        final = builder.sql_preview.toPlainText().strip()
        if final:
            self.sql_widget.setPlainText(final)

    def on_add(self):
        self.result_sql = self.sql_widget.toPlainText().strip()
        if not self.result_sql:
            QMessageBox.warning(self, 'Пустой SQL', 'Нельзя добавить пустой подзапрос.')
            return
        self.accept()

class ConditionDialog(QDialog):
    def __init__(self, columns, parent=None, title='Добавить условие'):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.columns = columns or []
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        self.col_cb = QComboBox()
        self.col_cb.addItems([f"{t}.{c}" for t, c in self.columns])
        self.where_operations = QComboBox()
        self.where_operations.addItems(['=', '!=', '<', '<=', '>', '>=', 'LIKE', '~', '~*', '!~', '!~*'])
        self.val_le = QLineEdit()
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(self.accept)
        layout.addRow('Столбец', self.col_cb)
        layout.addRow('Оператор', self.where_operations)
        layout.addRow('Значение', self.val_le)
        layout.addRow(add_btn)

    def get_condition(self):
        val = self.val_le.text().replace("'", "''")
        col = self.col_cb.currentText() if self.col_cb.currentIndex() >= 0 else ''
        op = self.where_operations.currentText() if self.where_operations.currentIndex() >= 0 else '='
        if col == '':
            return "1=1"
        return f"{col} {op} '{val}'"

class ConditionTypeDialog(QDialog):
    def __init__(self, columns, db=None, parent=None, title='Добавить условие'):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.columns = columns or []
        self.db = db
        self.result_condition = None
        self.setup_ui()

    def setup_ui(self):
        layout = QFormLayout(self)
        self.type_cb = QComboBox()
        self.type_cb.addItems(['Обычное условие', 'Подзапрос'])
        layout.addRow('Тип', self.type_cb)
        self.normal_btn = QPushButton('Добавить обычное условие')
        self.normal_btn.clicked.connect(self.open_normal_condition)
        self.subquery_widget = QWidget()
        sw_layout = QHBoxLayout(self.subquery_widget)
        self.op_cb = QComboBox()
        self.op_cb.addItems(['EXISTS', 'ANY', 'ALL'])
        self.col_cb = QComboBox()
        self.col_cb.addItems([f"{t}.{c}" for t, c in self.columns])
        self.compose_btn = QPushButton('Составить подзапрос')
        sw_layout.addWidget(self.op_cb)
        sw_layout.addWidget(self.col_cb)
        sw_layout.addWidget(self.compose_btn)
        self.compose_btn.clicked.connect(self.open_subquery_builder)
        self.op_cb.currentIndexChanged.connect(self.on_op_changed)
        layout.addRow(self.normal_btn)
        layout.addRow(self.subquery_widget)
        btn_row = QHBoxLayout()
        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)
        layout.addRow(btn_row)
        self.type_cb.currentIndexChanged.connect(self.on_type_changed)
        self.on_type_changed(0)

    def on_type_changed(self, idx):
        if idx == 0:
            self.normal_btn.setVisible(True)
            self.subquery_widget.setVisible(False)
        else:
            self.normal_btn.setVisible(False)
            self.subquery_widget.setVisible(True)
            self.on_op_changed(self.op_cb.currentIndex())

    def on_op_changed(self, idx):
        op = self.op_cb.currentText()
        if op == 'EXISTS':
            self.col_cb.setVisible(False)
        else:
            self.col_cb.setVisible(True)

    def open_normal_condition(self):
        dlg = ConditionDialog(self.columns, self, title=self.windowTitle())
        if dlg.exec():
            cond = dlg.get_condition()
            if cond:
                self.result_condition = cond
                self.accept()

    def open_subquery_builder(self):
        op = self.op_cb.currentText()
        col = self.col_cb.currentText() if self.col_cb.currentIndex() >= 0 else ''
        if op in ('ANY', 'ALL') and not col:
            QMessageBox.warning(self, 'Не выбран столбец', 'Для ANY/ALL нужно выбрать столбец.')
            return
        sqd = SubqueryDialog(db=self.db, parent=self)
        if sqd.exec():
            subq = sqd.result_sql
            if not subq:
                return
            if op == 'EXISTS':
                cond = f"EXISTS ({subq})"
            else:
                cond = f"{col} = {op} ({subq})"
            self.result_condition = cond
            self.accept()

    def get_condition(self):
        return self.result_condition


class CaseDialog(QDialog):
    def __init__(self, columns, db=None, parent=None, title='Создать CASE'):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.columns = columns or []
        self.db = db
        self.case_expression = ''
        self.when_rows = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.rows_scroll = QScrollArea()
        self.rows_scroll.setWidgetResizable(True)
        rows_container_widget = QWidget()
        self.rows_container = QVBoxLayout(rows_container_widget)
        rows_container_widget.setLayout(self.rows_container)
        self.rows_scroll.setWidget(rows_container_widget)
        layout.addWidget(self.rows_scroll)
        add_row_btn = QPushButton('Добавить условие')
        add_row_btn.clicked.connect(self.add_when_row)
        layout.addWidget(add_row_btn)
        else_layout = QFormLayout()
        self.else_le = QLineEdit()
        self.alias_le = QLineEdit()
        else_layout.addRow('ELSE', self.else_le)
        else_layout.addRow('Псевдоним (AS)', self.alias_le)
        layout.addLayout(else_layout)
        btn_row = QHBoxLayout()
        add_btn = QPushButton('Добавить')
        cancel_btn = QPushButton('Отмена')
        add_btn.clicked.connect(self.on_add)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(add_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)
        self.add_when_row()

    def add_when_row(self):
        row_w = QWidget()
        rlayout = QHBoxLayout(row_w)
        cond_label = QLabel('WHEN')
        set_cond_btn = QPushButton('Условие')
        then_le = QLineEdit()
        then_le.setPlaceholderText('THEN ')
        del_btn = QPushButton('Удалить')
        rlayout.addWidget(cond_label)
        rlayout.addWidget(set_cond_btn)
        rlayout.addWidget(QLabel('THEN'))
        rlayout.addWidget(then_le)
        rlayout.addWidget(del_btn)
        self.rows_container.addWidget(row_w)
        row_obj = {'widget': row_w, 'cond': None, 'cond_label': cond_label, 'then_widget': then_le}
        self.when_rows.append(row_obj)

        def set_condition():
            dlg = ConditionDialog(self.columns, self, title='Условие для WHEN')
            if dlg.exec():
                cond = dlg.get_condition()
                row_obj['cond'] = cond
                row_obj['cond_label'].setText(f"WHEN {cond}")

        def do_delete():
            try:
                self.when_rows.remove(row_obj)
            except ValueError:
                pass
            row_w.setParent(None)

        set_cond_btn.clicked.connect(set_condition)
        del_btn.clicked.connect(do_delete)

    def on_add(self):
        parts = []
        for row in list(self.when_rows):
            cond = row.get('cond')
            then_val = row.get('then_widget').text().strip() if row.get('then_widget') is not None else ''
            if cond and then_val:
                parts.append(f"WHEN {cond} THEN {then_val}")
        else_part = self.else_le.text().strip()
        alias = self.alias_le.text().strip() or 'case_expr'
        if not parts and not else_part:
            QMessageBox.warning(self, 'Пустой CASE', 'Добавьте хотя бы одно условие.')
            return
        expr = 'CASE ' + ' '.join(parts)
        if else_part:
            expr += ' ELSE ' + else_part
        expr += f' END AS {alias}'
        self.case_expression = expr
        self.accept()

    def get_expression(self):
        return self.case_expression


# --- Основной объединённый диалог (интерфейс из первого кода, логика — из второго) ---
class AdvancedSelectDialog(QDialog):
    apply_sql = Signal(str)

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Расширенный SELECT")
        self.setMinimumSize(1200, 750)

        # внутренние структуры, как во втором коде
        self.selected_columns = []  # list of (table, col)
        self.where_conditions = []
        self.having_conditions = []
        self.group_by = []
        self.order_by = []
        self.joins = []
        self.aggregates = []
        self.custom_expressions = []
        self.coalesce_rules = []
        self.schema = {}  # table -> [cols]

        self.setup_ui()
        self._load_schema()
        self.load_tables()
        self.load_columns_list()
        self.update_sql_preview()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.table_combo = QComboBox()
        top_layout.addWidget(QLabel("Таблица:"))
        top_layout.addWidget(self.table_combo)

        self.refresh_btn = QPushButton("Обновить")
        self.refresh_btn.clicked.connect(lambda: (self._load_schema(), self.load_tables(), self.load_columns_list()))
        top_layout.addWidget(self.refresh_btn)

        self.open_builder_btn = QPushButton("Открыть продвинутый билдeр")
        self.open_builder_btn.clicked.connect(self.open_sql_stub_window)
        top_layout.addWidget(self.open_builder_btn)

        top_layout.addStretch()
        layout.addLayout(top_layout)

        splitter = QSplitter(Qt.Horizontal)

        # ----- ЛЕВАЯ ПАНЕЛЬ (теперь в QScrollArea) -----
        left_content = QWidget()
        left_layout = QVBoxLayout(left_content)
        left_layout.setContentsMargins(6, 6, 6, 6)
        left_layout.setSpacing(8)

        columns_group = QGroupBox("Выбор столбцов")
        columns_layout = QVBoxLayout()
        self.columns_list = QListWidget()
        self.columns_list.setSelectionMode(QListWidget.MultiSelection)
        self.columns_list.itemSelectionChanged.connect(self.on_columns_selection_changed)
        columns_layout.addWidget(QLabel("Выберите столбцы для вывода:"))
        columns_layout.addWidget(self.columns_list)
        columns_group.setLayout(columns_layout)
        left_layout.addWidget(columns_group)

        expr_group = QGroupBox("Выражения")
        expr_layout = QVBoxLayout()
        self.expr_list = QListWidget()
        expr_layout.addWidget(self.expr_list)
        expr_btn_row = QHBoxLayout()
        create_case_btn = QPushButton('Создать CASE')
        create_case_btn.clicked.connect(self.open_case_builder)
        clear_expr_btn = QPushButton('Очистить')
        clear_expr_btn.clicked.connect(self.clear_expressions)
        expr_btn_row.addWidget(create_case_btn)
        expr_btn_row.addWidget(clear_expr_btn)
        expr_btn_row.addStretch()
        expr_layout.addLayout(expr_btn_row)
        expr_group.setLayout(expr_layout)
        left_layout.addWidget(expr_group)

        join_group = QGroupBox("Соединения (JOIN)")
        jlayout = QVBoxLayout()
        self.join_list = QListWidget()
        jlayout.addWidget(self.join_list)
        jbtn_row = QHBoxLayout()
        add_join_btn = QPushButton('Добавить JOIN')
        add_join_btn.clicked.connect(self.open_add_join_dialog)
        remove_join_btn = QPushButton('Удалить JOIN')
        remove_join_btn.clicked.connect(self.remove_selected_join)
        clear_join_btn = QPushButton('Очистить')
        clear_join_btn.clicked.connect(self.clear_join)
        jbtn_row.addWidget(add_join_btn)
        jbtn_row.addWidget(remove_join_btn)
        jbtn_row.addWidget(clear_join_btn)
        jbtn_row.addStretch()
        jlayout.addLayout(jbtn_row)
        join_group.setLayout(jlayout)
        left_layout.addWidget(join_group)

        where_group = QGroupBox("Условия WHERE")
        where_layout = QVBoxLayout()
        self.where_list = QListWidget()
        where_layout.addWidget(self.where_list)
        wbtn_row = QHBoxLayout()
        add_normal_where_btn = QPushButton('Обычное условие')
        add_normal_where_btn.clicked.connect(self.add_normal_where_condition)
        add_subquery_where_btn = QPushButton('Подзапрос')
        add_subquery_where_btn.clicked.connect(self.add_subquery_where_condition)
        remove_where_btn = QPushButton('Удалить WHERE')
        remove_where_btn.clicked.connect(self.remove_selected_where)
        clear_where_btn = QPushButton('Очистить')
        clear_where_btn.clicked.connect(self.clear_where)
        wbtn_row.addWidget(add_normal_where_btn)
        wbtn_row.addWidget(add_subquery_where_btn)
        wbtn_row.addWidget(remove_where_btn)
        wbtn_row.addWidget(clear_where_btn)
        wbtn_row.addStretch()
        where_layout.addLayout(wbtn_row)
        where_group.setLayout(where_layout)
        left_layout.addWidget(where_group)

        group_group = QGroupBox("Группировка (GROUP BY / агрегаты)")
        group_layout = QVBoxLayout()
        self.group_list = QListWidget()
        group_layout.addWidget(self.group_list)
        gbtn_row = QHBoxLayout()
        add_group_btn = QPushButton('Добавить GROUP BY')
        add_group_btn.clicked.connect(self.add_group_by)
        add_agg_btn = QPushButton('Добавить агрегат')
        add_agg_btn.clicked.connect(self.add_aggregate)
        remove_group_btn = QPushButton('Удалить')
        remove_group_btn.clicked.connect(self.remove_selected_group_or_agg)
        clear_group_btn = QPushButton('Очистить')
        clear_group_btn.clicked.connect(self.clear_group_by)
        gbtn_row.addWidget(add_group_btn)
        gbtn_row.addWidget(add_agg_btn)
        gbtn_row.addWidget(remove_group_btn)
        gbtn_row.addWidget(clear_group_btn)
        gbtn_row.addStretch()
        group_layout.addLayout(gbtn_row)
        group_group.setLayout(group_layout)
        left_layout.addWidget(group_group)

        having_group = QGroupBox("HAVING")
        hlay = QVBoxLayout()
        self.having_list = QListWidget()
        hlay.addWidget(self.having_list)
        hbtn_row = QHBoxLayout()
        add_having_btn = QPushButton('Добавить HAVING')
        add_having_btn.clicked.connect(self.add_having)
        remove_having_btn = QPushButton('Удалить HAVING')
        remove_having_btn.clicked.connect(self.remove_selected_having)
        clear_having_btn = QPushButton('Очистить')
        clear_having_btn.clicked.connect(self.clear_having)
        hbtn_row.addWidget(add_having_btn)
        hbtn_row.addWidget(remove_having_btn)
        hbtn_row.addWidget(clear_having_btn)
        hbtn_row.addStretch()
        hlay.addLayout(hbtn_row)
        having_group.setLayout(hlay)
        left_layout.addWidget(having_group)

        order_group = QGroupBox("ORDER BY")
        ol = QVBoxLayout()
        self.order_list = QListWidget()
        ol.addWidget(self.order_list)
        obtn_row = QHBoxLayout()
        add_order_btn = QPushButton('Добавить ORDER BY')
        add_order_btn.clicked.connect(self.add_order_by)
        remove_order_btn = QPushButton('Удалить ORDER BY')
        remove_order_btn.clicked.connect(self.remove_selected_order)
        clear_order_btn = QPushButton('Очистить')
        clear_order_btn.clicked.connect(self.clear_order_by)
        obtn_row.addWidget(add_order_btn)
        obtn_row.addWidget(remove_order_btn)
        obtn_row.addWidget(clear_order_btn)
        obtn_row.addStretch()
        ol.addLayout(obtn_row)
        order_group.setLayout(ol)
        left_layout.addWidget(order_group)

        # ----------------- Блок COALESCE / NULLIF -----------------
        coalesce_group = QGroupBox("COALESCE / NULLIF (замены)")
        coalesce_layout = QVBoxLayout()
        self.coalesce_list = QListWidget()
        coalesce_layout.addWidget(QLabel("Правила (operator, column, arg):"))
        coalesce_layout.addWidget(self.coalesce_list)
        co_btn_row = QHBoxLayout()
        add_co_btn = QPushButton("Добавить")
        del_co_btn = QPushButton("Удалить")
        apply_co_btn = QPushButton("Применить")
        clear_co_btn = QPushButton("Очистить")
        co_btn_row.addWidget(add_co_btn)
        co_btn_row.addWidget(del_co_btn)
        co_btn_row.addWidget(apply_co_btn)
        co_btn_row.addWidget(clear_co_btn)
        co_btn_row.addStretch()
        coalesce_layout.addLayout(co_btn_row)
        coalesce_group.setLayout(coalesce_layout)
        left_layout.addWidget(coalesce_group)

        # подключаем обработчики
        add_co_btn.clicked.connect(self.open_coalesce_dialog)
        del_co_btn.clicked.connect(self.remove_selected_coalesce)
        apply_co_btn.clicked.connect(self.apply_coalesce)
        clear_co_btn.clicked.connect(self.clear_coalesce)

        left_layout.addStretch()

        # Помещаем left_content в QScrollArea, чтобы появилась прокрутка
        left_scroll = QScrollArea()
        left_scroll.setWidgetResizable(True)
        left_scroll.setWidget(left_content)
        # Можно задать минимальную ширину, чтобы содержимое не съезжало
        left_scroll.setMinimumWidth(360)

        # ----- ПРАВАЯ ПАНЕЛЬ -----
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        self.sql_preview = QTextEdit()
        self.sql_preview.setMaximumHeight(120)
        right_layout.addWidget(QLabel("SQL запрос:"))
        right_layout.addWidget(self.sql_preview)

        btns_row = QHBoxLayout()
        self.apply_btn = QPushButton("Применить (emit)")
        self.apply_btn.clicked.connect(self.on_apply_clicked)
        self.execute_btn = QPushButton("Выполнить запрос")
        self.execute_btn.clicked.connect(self.execute_query)
        self.clear_btn = QPushButton("Очистить форму")
        self.clear_btn.clicked.connect(self.clear_all)
        self.close_btn = QPushButton("Закрыть")
        self.close_btn.clicked.connect(self.reject)
        btns_row.addWidget(self.apply_btn)
        btns_row.addWidget(self.execute_btn)
        btns_row.addWidget(self.clear_btn)
        btns_row.addWidget(self.close_btn)
        right_layout.addLayout(btns_row)

        self.result_table = QTableWidget()
        right_layout.addWidget(self.result_table)

        # Добавляем прокручиваемую левую панель и правую панель в splitter
        splitter.addWidget(left_scroll)
        splitter.addWidget(right_widget)
        splitter.setSizes([420, 480])
        layout.addWidget(splitter)

        self.table_combo.currentTextChanged.connect(self.load_columns_list)

    # --- Загрузка схемы из БД (вендор-независимо) ---
    def _load_schema(self):
        """
        Загружает схему из DBManager через list_tables() + get_table().
        Ожидает, что DBManager возвращает объекты таблиц с атрибутом .columns,
        где каждый элемент имеет .name.
        Записывает результат в self.schema (dict table -> [col1, col2, ...]).
        """
        schema = {}
        try:
            tables = []
            try:
                tables = self.db_manager.list_tables() or []
            except Exception as e:
                logging.error(f"Ошибка DBManager.list_tables(): {e}")
                tables = []

            for t in tables:
                try:
                    table_obj = self.db_manager.get_table(t)
                    if table_obj is None:
                        # если get_table вернул None — логируем и пропускаем
                        logging.debug(f"DBManager.get_table('{t}') вернул None")
                        continue
                    # ожидаем, что table_obj.columns — iterable объектов с .name
                    cols = []
                    for c in getattr(table_obj, "columns", []) or []:
                        # допускаем как SimpleNamespace(name=..), так и обычные строки
                        if hasattr(c, "name"):
                            cols.append(c.name)
                        else:
                            cols.append(str(c))
                    schema[t] = cols
                except Exception as e:
                    logging.exception(f"Ошибка получения метаданных таблицы {t}: {e}")
                    # пропускаем проблемную таблицу
                    continue

        except Exception as e:
            logging.exception(f"Неожиданная ошибка при загрузке схемы: {e}")

        self.schema = schema or {}

    def load_tables(self):
        """
        Заполняет self.table_combo только через DBManager.list_tables().
        """
        try:
            self.table_combo.blockSignals(True)
            self.table_combo.clear()
            tables = []
            try:
                tables = self.db_manager.list_tables() or []
            except Exception as e:
                logging.error(f"Ошибка вызова DBManager.list_tables(): {e}")
                tables = []

            for t in sorted(tables):
                self.table_combo.addItem(t)

            # Если есть таблицы — выставим первую по умолчанию
            if self.table_combo.count() > 0 and self.table_combo.currentIndex() < 0:
                self.table_combo.setCurrentIndex(0)

        except Exception as e:
            logging.exception(f"load_tables error: {e}")
        finally:
            self.table_combo.blockSignals(False)

    def load_columns_list(self):
        """
        Загружает колонки для выбранной в table_combo таблицы,
        используя строго DBManager.get_columns()/get_table().
        Обновляет self.columns_list и не стирает ранее выбранные колонки из других таблиц.
        """
        table_name = self.table_combo.currentText()
        self.columns_list.clear()
        if not table_name:
            return

        cols = []
        try:
            # сначала пробуем специализированный метод get_columns
            try:
                cols = self.db_manager.get_columns(table_name) or []
            except Exception as e:
                logging.debug(f"DBManager.get_columns('{table_name}') вызвал исключение: {e}")
                cols = []

            # если get_columns ничего не вернул, пробуем get_table()
            if not cols:
                try:
                    table_obj = self.db_manager.get_table(table_name)
                    if table_obj is not None:
                        cols = [c.name if hasattr(c, "name") else str(c) for c in
                                getattr(table_obj, "columns", []) or []]
                except Exception as e:
                    logging.debug(f"DBManager.get_table('{table_name}') вызвал исключение: {e}")
                    cols = []

        except Exception as e:
            logging.exception(f"Ошибка загрузки колонок для {table_name}: {e}")
            cols = []

        # Сохраняем набор уже выбранных пар (table, col)
        existing_selected = set(self.selected_columns)

        for c in cols:
            item = QListWidgetItem(c)
            self.columns_list.addItem(item)
            # если эта колонка была ранее выбрана — отметим её
            if (table_name, c) in existing_selected:
                item.setSelected(True)


        self.update_sql_preview()

    def add_normal_where_condition(self):
        # обычное условие через ConditionDialog
        cols = [(t, c) for t in self.schema for c in self.schema[t]]
        dlg = ConditionDialog(cols, self, title='Добавить обычное условие')
        if dlg.exec():
            cond = dlg.get_condition()
            if cond:
                self.where_conditions.append(cond)
                self.where_list.addItem(cond)
                self.update_sql_preview()

    def add_subquery_where_condition(self):

        dlg = QDialog(self)
        dlg.setWindowTitle('Добавить условие-подзапрос')
        layout = QFormLayout(dlg)

        op_cb = QComboBox()
        op_cb.addItems(['EXISTS', 'ANY', 'ALL'])
        col_cb = QComboBox()
        col_cb.addItems([f"{t}.{c}" for t in self.schema for c in self.schema[t]])
        cmp_cb = QComboBox()
        cmp_cb.addItems(['=', '!=', '<', '<=', '>', '>=', 'LIKE', '~', '~*', '!~', '!~*'])
        sql_text = QTextEdit()
        sql_text.setPlaceholderText('SQL подзапрос появится здесь после составления или вставки...')

        compose_btn = QPushButton('Составить подзапрос')

        def do_compose():
            builder = AdvancedSelectDialog(self.db_manager, parent=self)

            # при emit переносим sql в поле сразу
            def on_apply_sql(sql):
                if sql:
                    sql_text.setPlainText(sql)

            builder.apply_sql.connect(on_apply_sql)
            builder.exec()
            final = builder.sql_preview.toPlainText().strip()
            if final:
                sql_text.setPlainText(final)

        compose_btn.clicked.connect(do_compose)

        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(dlg.accept)
        cancel_btn = QPushButton('Отмена')
        cancel_btn.clicked.connect(dlg.reject)

        # Размещение виджетов
        layout.addRow('Оператор', op_cb)
        layout.addRow('Столбец (для ANY/ALL)', col_cb)
        layout.addRow('Оператор сравнения (для ANY/ALL)', cmp_cb)
        layout.addRow(compose_btn)
        layout.addRow(QLabel('Подзапрос (SELECT ...):'))
        layout.addRow(sql_text)
        btn_row = QHBoxLayout()
        btn_row.addWidget(add_btn)
        btn_row.addWidget(cancel_btn)
        layout.addRow(btn_row)

        def on_op_changed(idx):
            op = op_cb.currentText()
            if op == 'EXISTS':
                col_cb.setVisible(False)
                cmp_cb.setVisible(False)
            else:
                col_cb.setVisible(True)
                cmp_cb.setVisible(True)

        op_cb.currentIndexChanged.connect(on_op_changed)
        on_op_changed(op_cb.currentIndex())

        if dlg.exec():
            subq = sql_text.toPlainText().strip()
            op = op_cb.currentText()
            col = col_cb.currentText() if col_cb.currentIndex() >= 0 else ''
            comp = cmp_cb.currentText() if cmp_cb.currentIndex() >= 0 else '='

            if not subq:
                QMessageBox.warning(self, 'Пустой подзапрос', 'Сначала составьте или вставьте подзапрос.')
                return

            if op == 'EXISTS':
                cond = f"EXISTS ({subq})"
            else:
                if not col:
                    QMessageBox.warning(self, 'Не выбран столбец', 'Для ANY/ALL нужно выбрать столбец.')
                    return
                cond = f"{col} {comp} {op} ({subq})"

            self.where_conditions.append(cond)
            self.where_list.addItem(cond)
            self.update_sql_preview()
    def execute_query(self):

        sql = self.sql_preview.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "Пустой SQL", "Сначала составьте SQL.")
            return

        try:
            cur = None
            try:
                cur = self.db_manager.execute(sql)
                if not cur:
                    QMessageBox.warning(self, "Ошибка", "DBManager.execute вернул None — запрос не выполнен.")
                    return

                try:
                    rows = cur.fetchall()
                except Exception:
                    try:
                        rows = []
                    except Exception:
                        rows = []

                desc = getattr(cur, "description", None)
                columns = [d[0] for d in desc] if desc else []

                self.result_table.setRowCount(len(rows))
                self.result_table.setColumnCount(len(columns))
                if columns:
                    self.result_table.setHorizontalHeaderLabels(columns)
                for row_idx, row_data in enumerate(rows):
                    for col_idx, cell_data in enumerate(row_data):
                        item = QTableWidgetItem(str(cell_data) if cell_data is not None else "")
                        self.result_table.setItem(row_idx, col_idx, item)
            finally:
                try:
                    if cur is not None:
                        cur.close()
                except Exception:
                    pass

        except Exception as e:
            logging.exception(f"Ошибка выполнения запроса: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка выполнения запроса:\n{str(e)}")

    def on_columns_selection_changed(self):
        table = self.table_combo.currentText()
        current_selected = [(table, it.text()) for it in self.columns_list.selectedItems()]


        try:
            self.selected_columns = [sc for sc in self.selected_columns if sc[0] != table]
        except Exception:
            self.selected_columns = []

        self.selected_columns.extend(current_selected)
        self.update_sql_preview()

    def open_case_builder(self):
        cols = [(t, c) for t in self.schema for c in self.schema[t]]
        dlg = CaseDialog(cols, db=self.db_manager, parent=self, title='Создать CASE')
        if dlg.exec():
            expr = dlg.get_expression()
            if expr:
                self.custom_expressions.append(expr)
                self.expr_list.addItem(expr)
                self.update_sql_preview()

    def clear_expressions(self):
        self.custom_expressions.clear()
        self.expr_list.clear()
        self.update_sql_preview()

    def open_add_join_dialog(self):
        dlg = JoinDialog(self.schema, self)
        if dlg.exec():
            j = dlg.get_join()
            if j['left'] and j['right'] and j['lf'] and j['rf']:
                self.joins.append(j)
                self.join_list.addItem(j['desc'])
                QMessageBox.information(self, 'Соединение добавлено', f"Добавлено: {j['desc']}")
                self.update_sql_preview()
            else:
                QMessageBox.warning(self, 'Соединение не добавлено', 'Выберите таблицы и поля для соединения.')

    def remove_selected_join(self):
        row = self.join_list.currentRow()
        if row >= 0:
            self.join_list.takeItem(row)
            try:
                del self.joins[row]
            except Exception:
                pass
            self.update_sql_preview()

    def clear_join(self):
        self.join_list.clear()
        self.joins.clear()
        self.update_sql_preview()

    def add_where_condition(self):
        cols = [(t, c) for t in self.schema for c in self.schema[t]]
        dlg = ConditionTypeDialog(cols, db=self.db_manager, parent=self, title='Добавить WHERE-условие')
        if dlg.exec():
            cond = dlg.get_condition()
            if cond:
                self.where_conditions.append(cond)
                self.where_list.addItem(cond)
                self.update_sql_preview()

    def remove_selected_where(self):
        row = self.where_list.currentRow()
        if row >= 0:
            self.where_list.takeItem(row)
            try:
                del self.where_conditions[row]
            except Exception:
                pass
            self.update_sql_preview()

    def clear_where(self):
        self.where_list.clear()
        self.where_conditions.clear()
        self.update_sql_preview()

    def add_group_by(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("GROUP BY")
        dlg.resize(500, 450)
        
        layout = QVBoxLayout(dlg)
        
        # Выбор типа группировки
        type_layout = QFormLayout()
        type_cb = QComboBox()
        type_cb.addItems(["Обычная группировка", "ROLLUP", "CUBE", "GROUPING SETS"])
        type_layout.addRow("Тип группировки:", type_cb)
        layout.addLayout(type_layout)
        
        # Список для выбора столбцов
        layout.addWidget(QLabel("Выберите столбцы для группировки:"))
        columns_list = QListWidget()
        columns_list.setSelectionMode(QListWidget.MultiSelection)
        
        # Заполняем список доступными столбцами
        for t in sorted(self.schema.keys()):
            for c in self.schema[t]:
                columns_list.addItem(f"{t}.{c}")
        
        layout.addWidget(columns_list)
        
        # Информация о выбранном типе
        info_label = QLabel()
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #555; padding: 10px; background-color: #f0f0f0; border-radius: 5px;")
        layout.addWidget(info_label)
        
        def update_info():
            selected_type = type_cb.currentText()
            if selected_type == "ROLLUP":
                info_label.setText(
                    " ROLLUP создает иерархические подитоги.\n"
                    "Например, для (отдел, должность) создаст группировки:\n"
                    "• (отдел, должность) - детальная группировка\n"
                    "• (отдел) - промежуточный итог по отделу\n"
                    "• () - общий итог"
                )
            elif selected_type == "CUBE":
                info_label.setText(
                    " CUBE создает все возможные комбинации группировок.\n"
                    "Например, для (регион, категория) создаст:\n"
                    "• (регион, категория)\n"
                    "• (регион)\n"
                    "• (категория)\n"
                    "• () - общий итог"
                )
            elif selected_type == "GROUPING SETS":
                info_label.setText(
                    " GROUPING SETS позволяет указать конкретные комбинации.\n"
                    "Каждый выбранный столбец будет отдельной группировкой.\n"
                    "Используется для создания специфических наборов группировок."
                )
            else:
                info_label.setText(
                    " Стандартная группировка по выбранным столбцам.\n"
                    "Все выбранные столбцы будут использованы в GROUP BY."
                )
        
        type_cb.currentIndexChanged.connect(update_info)
        update_info()
        
 
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")
        
        add_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        if dlg.exec():
            selected_items = columns_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Внимание", "Выберите хотя бы один столбец.")
                return
            
            selected_cols = [item.text() for item in selected_items]
            group_type = type_cb.currentText()
            
            if group_type == "Обычная группировка":
                for col in selected_cols:
                    self.groupby.append(col)
                    self.grouplist.addItem(col)
            
            elif group_type == "ROLLUP":
                cols_str = ", ".join(selected_cols)
                rollup_expr = f"ROLLUP({cols_str})"
                self.groupby.append(rollup_expr)
                self.grouplist.addItem(f"📊 ROLLUP: {cols_str}")
            
            elif group_type == "CUBE":
                cols_str = ", ".join(selected_cols)
                cube_expr = f"CUBE({cols_str})"
                self.groupby.append(cube_expr)
                self.grouplist.addItem(f"🧊 CUBE: {cols_str}")
            
            elif group_type == "GROUPING SETS":
                sets_parts = [f"({col})" for col in selected_cols]
                sets_str = ", ".join(sets_parts)
                grouping_sets_expr = f"GROUPING SETS({sets_str})"
                self.groupby.append(grouping_sets_expr)
                self.grouplist.addItem(f"🎯 GROUPING SETS: {', '.join(selected_cols)}")
            
            self.updatesqlpreview()


    def remove_selected_group_or_agg(self):
        row = self.group_list.currentRow()
        if row >= 0:
            self.group_list.takeItem(row)
            try:

                text = self.group_list.item(row).text() if self.group_list.count() > row else None
            except Exception:
                text = None
            try:
                if row < len(self.group_by):
                    del self.group_by[row]
                else:
                    agg_idx = row - max(0, len(self.group_by))
                    if 0 <= agg_idx < len(self.aggregates):
                        del self.aggregates[agg_idx]
            except Exception:
                pass
            self.update_sql_preview()

    def clear_group_by(self):
        self.group_list.clear()
        self.group_by.clear()
        self.aggregates.clear()
        self.update_sql_preview()

    def add_aggregate(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('Добавить агрегат')
        layout = QFormLayout(dlg)
        
        col_cb = QComboBox()
        col_cb.addItems([f"{t}.{c}" for t in self.schema for c in self.schema[t]])
        
        agg_cb = QComboBox()
        agg_cb.addItems(['COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'GROUPING'])
        
        alias_le = QLineEdit()
        
        info_label = QLabel()
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: gray; font-size: 9pt;")
        
        def update_info():
            if agg_cb.currentText() == 'GROUPING':
                info_label.setText(
                    "GROUPING() возвращает 1 для итоговых строк и 0 для обычных. "
                    "Используется с ROLLUP, CUBE или GROUPING SETS."
                )
            else:
                info_label.setText("")
        
        agg_cb.currentIndexChanged.connect(update_info)
        update_info()
        
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(dlg.accept)
        
        layout.addRow('Столбец:', col_cb)
        layout.addRow('Функция:', agg_cb)
        layout.addRow('Псевдоним:', alias_le)
        layout.addRow(info_label)
        layout.addRow(add_btn)
        
        if dlg.exec():
            fn = agg_cb.currentText()
            col = col_cb.currentText()
            alias = alias_le.text() or f"{fn.lower()}_{col.replace('.', '_')}"
            
            if col:
                self.aggregates.append((fn, col, alias))
                self.group_list.addItem(f"{fn}({col}) AS {alias}")
                self.update_sql_preview()


    def add_having(self):
        if not self.group_by and not self.aggregates:
            QMessageBox.warning(self, 'HAVING недоступно', 'Нужно добавить GROUP BY или агрегат перед использованием HAVING.')
            return
        cols = [(t, c) for t in self.schema for c in self.schema[t]]
        dlg = ConditionTypeDialog(cols, db=self.db_manager, parent=self, title='Добавить HAVING-условие')
        if dlg.exec():
            cond = dlg.get_condition()
            if cond:
                self.having_conditions.append(cond)
                self.having_list.addItem(cond)
                self.update_sql_preview()

    def remove_selected_having(self):
        row = self.having_list.currentRow()
        if row >= 0:
            self.having_list.takeItem(row)
            try:
                del self.having_conditions[row]
            except Exception:
                pass
            self.update_sql_preview()

    def clear_having(self):
        self.having_list.clear()
        self.having_conditions.clear()
        self.update_sql_preview()

    def add_order_by(self):
        dlg = QDialog(self)
        dlg.setWindowTitle('Добавить ORDER BY')
        layout = QFormLayout(dlg)
        col_cb = QComboBox()
        col_cb.addItems([f"{t}.{c}" for t in self.schema for c in self.schema[t]])
        dir_cb = QComboBox()
        dir_cb.addItems(['ASC', 'DESC'])
        add_btn = QPushButton('Добавить')
        add_btn.clicked.connect(dlg.accept)
        layout.addRow('Столбец', col_cb)
        layout.addRow('Направление', dir_cb)
        layout.addRow(add_btn)
        if dlg.exec():
            entry = f"{col_cb.currentText()} {dir_cb.currentText()}"
            if col_cb.currentText():
                self.order_by.append(entry)
                self.order_list.addItem(entry)
                self.update_sql_preview()

    def remove_selected_order(self):
        row = self.order_list.currentRow()
        if row >= 0:
            self.order_list.takeItem(row)
            try:
                del self.order_by[row]
            except Exception:
                pass
            self.update_sql_preview()

    def clear_order_by(self):
        self.order_list.clear()
        self.order_by.clear()
        self.update_sql_preview()

    def open_coalesce_dialog(self):

        dlg = QDialog(self)
        dlg.setWindowTitle("Добавить COALESCE/NULLIF правило")
        layout = QFormLayout(dlg)

        op_cb = QComboBox()
        op_cb.addItems(['COALESCE', 'NULLIF'])

        col_cb = QComboBox()
        cols = []
        for t in sorted(self.schema.keys()):
            for c in self.schema[t]:
                cols.append(f"{t}.{c}")
        col_cb.addItems(cols)

        arg_le = QLineEdit()
        arg_le.setPlaceholderText("значение второго аргумента (пример: unknown, 0 или NULL) — кавычки подставятся автоматически")

        add_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(add_btn)
        btn_row.addWidget(cancel_btn)

        layout.addRow('Оператор', op_cb)
        layout.addRow('Столбец', col_cb)
        layout.addRow('Второй аргумент', arg_le)
        layout.addRow(btn_row)

        cancel_btn.clicked.connect(dlg.reject)

        def do_add():
            op = op_cb.currentText()
            col = col_cb.currentText()
            raw_arg = arg_le.text().strip()
            if not col:
                QMessageBox.warning(dlg, "Ошибка", "Выберите столбец.")
                return
            formatted_arg = self._format_literal_arg(raw_arg)
            expr = f"{op}({col}, {formatted_arg})"
            rule = {'op': op, 'col': col, 'arg': formatted_arg, 'expr': expr}
            self.coalesce_rules.append(rule)
            self.coalesce_list.addItem(f"{op} | {col} | {formatted_arg}")
            dlg.accept()

        add_btn.clicked.connect(do_add)
        dlg.exec()

    def remove_selected_coalesce(self):

        sel_items = self.coalesce_list.selectedItems()
        if not sel_items:
            return
        reply = QMessageBox.question(self, "Удалить правило", "Удалить выбранные правила?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
        rows = sorted([self.coalesce_list.row(it) for it in sel_items], reverse=True)
        for r in rows:
            try:
                self.coalesce_list.takeItem(r)
            except Exception:
                pass
            try:
                del self.coalesce_rules[r]
            except Exception:
                pass

    def _regex_escape_col(self, col_name: str) -> str:

        return re.escape(col_name)

    def apply_coalesce(self):

        sql = self.sql_preview.toPlainText()
        if not sql:
            QMessageBox.warning(self, "Пустой SQL", "Нет SQL для применения замен.")
            return
        new_sql = sql
        for rule in self.coalesce_rules:
            col = rule['col']
            expr = rule['expr']
            pat = r'(?<![\w])' + self._regex_escape_col(col) + r'(?![\w])'
            new_sql = re.sub(pat, expr, new_sql)
        self.sql_preview.setPlainText(new_sql)
        QMessageBox.information(self, "Готово", "Применены COALESCE/NULLIF правила к SQL.")

    def _format_literal_arg(self, arg: str) -> str:

        if arg is None:
            return "NULL"
        s = str(arg).strip()
        if s == "":
            return "''"
        if s.upper() == "NULL":
            return "NULL"
        if (s.startswith("'") and s.endswith("'")) or (s.startswith('"') and s.endswith('"')):
            return s
        if re.fullmatch(r'[+-]?\d+(\.\d+)?', s):
            return s
        if s.lower() in ("true", "false", "t", "f", "yes", "no", "1", "0"):
            if s.lower() in ("true", "t", "yes", "1"):
                return "TRUE"
            if s.lower() in ("false", "f", "no", "0"):
                return "FALSE"
        esc = s.replace("'", "''")
        return f"'{esc}'"

    def clear_coalesce(self):

        sql = self.sql_preview.toPlainText()
        if not sql:
            QMessageBox.warning(self, "Пустой SQL", "Нет SQL для очистки.")
            return
        new_sql = sql
        for rule in self.coalesce_rules:
            expr = rule['expr']

            esc = re.escape(expr)
            esc_flexible = esc.replace(r'\,', r'\s*,\s*')
            try:
                new_sql = re.sub(esc_flexible, rule['col'], new_sql)
            except re.error:
                new_sql = new_sql.replace(expr, rule['col'])
        self.sql_preview.setPlainText(new_sql)
        QMessageBox.information(self, "Готово", "COALESCE/NULLIF правила убраны (по возможности).")


    def build_sql(self) -> str:
        parts = []
        if self.selected_columns:
            parts.extend([f"{t}.{c}" for t, c in self.selected_columns])
        if self.aggregates:
            for fn, col, alias in self.aggregates:
                parts.append(f"{fn}({col}) AS {alias}")
        if self.custom_expressions:
            parts.extend(self.custom_expressions)
        select_clause = ', '.join(parts) if parts else '*'

        sql_lines = []
        sql_lines.append(f"SELECT {select_clause}")

        from_clause = ""
        join_clauses = []
        if self.joins:
            base_table = self.joins[0].get('left') or ''
            if base_table:
                from_clause = base_table
            for j in self.joins:
                left = j.get('left', '')
                right = j.get('right', '')
                lf = j.get('lf', '')
                rf = j.get('rf', '')
                jtype = j.get('type', 'INNER')
                if right:
                    join_clauses.append(f"{jtype} JOIN {right} ON {left}.{lf} = {right}.{rf}")
        else:
            tables = set(t for t, _ in self.selected_columns)
            if len(tables) >= 1:
                if len(tables) == 1:
                    from_clause = next(iter(tables))
                else:
                    from_clause = ', '.join(sorted(tables))
            else:
                table_selected = self.table_combo.currentText()
                if table_selected:
                    from_clause = table_selected
                else:
                    all_tables = sorted(self.schema.keys())
                    from_clause = all_tables[0] if all_tables else ''

        if from_clause:
            sql_lines.append(f"FROM {from_clause}")
        else:
            sql_lines.append("FROM /* no table selected */")

        sql_lines.extend(join_clauses)

        if self.where_conditions:
            sql_lines.append("WHERE " + " AND ".join(self.where_conditions))

        if self.group_by:
            sql_lines.append("GROUP BY " + ", ".join(self.group_by))

        if self.having_conditions:
            sql_lines.append("HAVING " + " AND ".join(self.having_conditions))

        if self.order_by:
            sql_lines.append("ORDER BY " + ", ".join(self.order_by))

        return "\n".join(sql_lines)

    def update_sql_preview(self):
        try:
            s = self.build_sql()
        except Exception as e:
            s = f"Error: {e}"
        self.sql_preview.setPlainText(s)

    def on_apply_clicked(self):
        try:
            self.update_sql_preview()
        except Exception:
            pass
        sql = self.sql_preview.toPlainText().strip()
        if not sql:
            QMessageBox.warning(self, "Пустой SQL", "SQL пустой — нечего применять.")
            return
        self.apply_sql.emit(sql)


    def open_sql_stub_window(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Продвинутый билдер SQL (встроенный)")
        dlg.resize(800, 600)
        layout = QVBoxLayout(dlg)

        builder_widget = QWidget()
        b_layout = QVBoxLayout(builder_widget)
        sql_view = QTextEdit()
        sql_view.setReadOnly(True)
        def refresh_builder_sql():
            try:
                s = self.build_sql()
            except Exception as e:
                s = f"Error: {e}"
            sql_view.setPlainText(s)
        refresh_builder_sql()

        btn_row = QHBoxLayout()
        apply_btn = QPushButton("Применить (в основное поле)")
        apply_btn.clicked.connect(lambda: (self.sql_preview.setPlainText(sql_view.toPlainText()), dlg.accept()))
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(refresh_builder_sql)
        btn_row.addWidget(apply_btn)
        btn_row.addWidget(refresh_btn)
        btn_row.addStretch()
        b_layout.addWidget(sql_view)
        b_layout.addLayout(btn_row)
        layout.addWidget(builder_widget)
        dlg.exec()

    def clear_all(self):
        self.columns_list.clearSelection()
        self.selected_columns = []
        self.where_list.clear()
        self.where_conditions = []
        self.group_list.clear()
        self.group_by = []
        self.aggregates = []
        self.having_list.clear()
        self.having_conditions = []
        self.order_list.clear()
        self.order_by = []
        self.join_list.clear()
        self.joins = []
        self.expr_list.clear()
        self.custom_expressions = []
        self.result_table.setRowCount(0)
        self.result_table.setColumnCount(0)
        self.sql_preview.clear()
        self.update_sql_preview()
    def addgroupby(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("GROUP BY")
        dlg.resize(500, 400)
        
        layout = QVBoxLayout(dlg)
        
        # Выбор типа группировки
        type_layout = QFormLayout()
        type_cb = QComboBox()
        type_cb.addItems(["Обычная группировка", "ROLLUP", "CUBE", "GROUPING SETS"])
        type_layout.addRow("Тип группировки:", type_cb)
        layout.addLayout(type_layout)
        
        # Список для выбора столбцов
        layout.addWidget(QLabel("Выберите столбцы для группировки:"))
        columns_list = QListWidget()
        columns_list.setSelectionMode(QListWidget.MultiSelection)
        
        # Заполняем список доступными столбцами
        for t in sorted(self.schema.keys()):
            for c in self.schema[t]:
                columns_list.addItem(f"{t}.{c}")
        
        layout.addWidget(columns_list)
        
        # Информация о выбранном типе
        info_label = QLabel()
        info_label.setWordWrap(True)
        layout.addWidget(info_label)
        
        def update_info():
            selected_type = type_cb.currentText()
            if selected_type == "ROLLUP":
                info_label.setText(
                    "ROLLUP создает иерархические подитоги. "
                    "Например, для (a, b, c) создаст группировки: (a,b,c), (a,b), (a), ()."
                )
            elif selected_type == "CUBE":
                info_label.setText(
                    "CUBE создает все возможные комбинации группировок. "
                    "Например, для (a, b) создаст: (a,b), (a), (b), ()."
                )
            elif selected_type == "GROUPING SETS":
                info_label.setText(
                    "GROUPING SETS позволяет указать конкретные комбинации группировок. "
                    "Каждый выбранный столбец будет отдельной группировкой."
                )
            else:
                info_label.setText("Стандартная группировка по выбранным столбцам.")
        
        type_cb.currentIndexChanged.connect(update_info)
        update_info()
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Добавить")
        cancel_btn = QPushButton("Отмена")
        
        add_btn.clicked.connect(dlg.accept)
        cancel_btn.clicked.connect(dlg.reject)
        
        btn_layout.addStretch()
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addLayout(btn_layout)
        
        if dlg.exec():
            selected_items = columns_list.selectedItems()
            if not selected_items:
                QMessageBox.warning(self, "Внимание", "Выберите хотя бы один столбец.")
                return
            
            selected_cols = [item.text() for item in selected_items]
            group_type = type_cb.currentText()
            
            if group_type == "Обычная группировка":
                for col in selected_cols:
                    self.groupby.append(col)
                    self.grouplist.addItem(col)
            
            elif group_type == "ROLLUP":
                cols_str = ", ".join(selected_cols)
                rollup_expr = f"ROLLUP({cols_str})"
                self.groupby.append(rollup_expr)
                self.grouplist.addItem(f"ROLLUP: {cols_str}")
            
            elif group_type == "CUBE":
                cols_str = ", ".join(selected_cols)
                cube_expr = f"CUBE({cols_str})"
                self.groupby.append(cube_expr)
                self.grouplist.addItem(f"CUBE: {cols_str}")
            
            elif group_type == "GROUPING SETS":
                sets_parts = [f"({col})" for col in selected_cols]
                sets_str = ", ".join(sets_parts)
                grouping_sets_expr = f"GROUPING SETS({sets_str})"
                self.groupby.append(grouping_sets_expr)
                self.grouplist.addItem(f"GROUPING SETS: {', '.join(selected_cols)}")
            
            self.updatesqlpreview()
