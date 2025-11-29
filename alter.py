from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QLabel, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QTabWidget, QWidget, QGroupBox, QInputDialog, QCheckBox,
    QListWidget, QListWidgetItem, QSplitter, QFrame)
from PySide6.QtCore import Qt
import logging


class TableMetadataDialog(QDialog):
    def __init__(self, db_manager, table_name, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.table_name = table_name
        self.setWindowTitle(f"Метаданные: {table_name}")
        self.resize(700, 400)
        layout = QVBoxLayout(self)
        text = []
        cols = []
        try:
            cols = self.db_manager.get_columns(table_name) or []
        except Exception:
            cols = []
        if not cols:
            layout.addWidget(QLabel("Нет колонок или не удалось получить список колонок."))
            return
        for c in cols:
            md = {}
            try:
                md = self.db_manager.get_column_metadata(table_name, c) or {}
            except Exception:
                md = {}
            lines = [f"{table_name}.{c}"]
            lines.append(f"  type: {md.get('data_type')}, nullable: {md.get('is_nullable')}, default: {md.get('column_default')}")
            if md.get('is_primary'):
                lines.append("  PRIMARY KEY")
            for u in md.get('unique_constraints', []):
                lines.append(f"  UNIQUE: {u.get('name')} cols={u.get('columns')}")
            for ch in md.get('check_constraints', []):
                lines.append(f"  CHECK: {ch.get('name')} expr={ch.get('expr')}")
            for fk in md.get('foreign_keys', []):
                lines.append(f"  FK: {fk.get('name')} -> {fk.get('ref_table')}({fk.get('ref_columns')})")
            text.append("\n".join(lines))
        from PySide6.QtWidgets import QTextEdit, QPushButton
        te = QTextEdit()
        te.setReadOnly(True)
        te.setPlainText("\n\n".join(text))
        layout.addWidget(te)
        btn = QPushButton("Закрыть")
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)


class AlterTableDialog(QDialog):
    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Изменение структуры таблиц")
        self.setMinimumSize(720, 520)

        self.setup_ui()
        self.load_tables()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.table_combo = QComboBox()
        form.addRow("Таблица:", self.table_combo)

        self.table_meta_btn = QPushButton("Показать метаданные таблицы")
        self.table_meta_btn.clicked.connect(self.on_show_table_metadata)
        form.addRow(self.table_meta_btn)

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
        self.operation_combo.currentTextChanged.connect(self.update_params_form)
        form.addRow("Операция:", self.operation_combo)

        layout.addLayout(form)

        self.params_widget = QWidget()
        self.params_layout = QFormLayout(self.params_widget)
        layout.addWidget(self.params_widget)

        row = QHBoxLayout()
        self.execute_btn = QPushButton("Выполнить")
        self.execute_btn.clicked.connect(self.on_execute_clicked)
        self.preview_btn = QPushButton("Показать пример SQL")
        self.preview_btn.clicked.connect(self.on_preview_clicked)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        row.addWidget(self.execute_btn)
        row.addWidget(self.preview_btn)
        row.addWidget(self.cancel_btn)
        layout.addLayout(row)


        self.update_params_form()

    def load_tables(self):
        self.table_combo.clear()
        try:
            tables = self.db_manager.list_tables() or []
        except Exception:
            tables = []
        for t in sorted(tables):
            self.table_combo.addItem(t)
        if self.table_combo.count():
            self.table_combo.setCurrentIndex(0)

    def clear_params_layout(self):
        while self.params_layout.rowCount():
            self.params_layout.removeRow(0)

    def update_params_form(self):
        self.clear_params_layout()
        op = self.operation_combo.currentText()
        table = self.table_combo.currentText()

        if op == "Добавить столбец":
            self.col_name_le = QLineEdit()
            self.type_cb = QComboBox()
            self.type_cb.addItems(["VARCHAR(255)", "INTEGER", "DECIMAL(10,2)", "DATE", "BOOLEAN", "TEXT", "TIMESTAMP"])
            self.notnull_cb = QCheckBox("NOT NULL")
            self.default_le = QLineEdit()
            self.unique_cb = QCheckBox("UNIQUE")
            self.constraint_name_le = QLineEdit()
            self.constraint_name_le.setPlaceholderText("Имя ограничения (опционально)")
            self.params_layout.addRow("Имя столбца:", self.col_name_le)
            self.params_layout.addRow("Тип:", self.type_cb)
            self.params_layout.addRow(self.notnull_cb)
            self.params_layout.addRow("DEFAULT (SQL literal):", self.default_le)
            self.params_layout.addRow(self.unique_cb)
            self.params_layout.addRow("Имя ограничения:", self.constraint_name_le)

        elif op == "Удалить столбец":
            self.column_cb = QComboBox()
            cols = self.db_manager.get_columns(table) or []
            self.column_cb.addItems(cols)
            self.params_layout.addRow("Столбец:", self.column_cb)

        elif op == "Переименовать таблицу":
            self.new_table_le = QLineEdit()
            self.params_layout.addRow("Новое имя:", self.new_table_le)

        elif op == "Переименовать столбец":
            self.old_col_cb = QComboBox()
            cols = self.db_manager.get_columns(table) or []
            self.old_col_cb.addItems(cols)
            self.new_col_le = QLineEdit()
            self.params_layout.addRow("Текущий столбец:", self.old_col_cb)
            self.params_layout.addRow("Новое имя:", self.new_col_le)

        elif op == "Изменить тип данных":
            self.col_cb = QComboBox()
            cols = self.db_manager.get_columns(table) or []
            self.col_cb.addItems(cols)
            self.new_type_cb = QComboBox()
            self.new_type_cb.addItems(["VARCHAR(255)", "INTEGER", "DECIMAL(10,2)", "DATE", "BOOLEAN", "TEXT", "TIMESTAMP"])
            self.new_notnull_cb = QCheckBox("SET NOT NULL")
            self.new_default_le = QLineEdit()
            self.new_unique_cb = QCheckBox("UNIQUE (после смены типа)")
            self.new_fk_table_cb = QComboBox()
            try:
                ref_tables = self.db_manager.list_tables() or []
            except Exception:
                ref_tables = []
            self.new_fk_table_cb.addItems([""] + ref_tables)
            self.new_fk_col_cb = QComboBox()
            def on_ref_table_changed(idx):
                rt = self.new_fk_table_cb.currentText()
                self.new_fk_col_cb.clear()
                if rt:
                    try:
                        self.new_fk_col_cb.addItems(self.db_manager.get_columns(rt) or [])
                    except Exception:
                        pass
            self.new_fk_table_cb.currentIndexChanged.connect(on_ref_table_changed)

            self.params_layout.addRow("Столбец:", self.col_cb)
            self.params_layout.addRow("Новый тип:", self.new_type_cb)
            self.params_layout.addRow(self.new_notnull_cb)
            self.params_layout.addRow("DEFAULT (SQL literal):", self.new_default_le)
            self.params_layout.addRow(self.new_unique_cb)
            self.params_layout.addRow("FK: ref table:", self.new_fk_table_cb)
            self.params_layout.addRow("FK: ref column:", self.new_fk_col_cb)

        elif op == "Добавить ограничение":
            self.constraint_type_cb = QComboBox()
            self.constraint_type_cb.addItems(["NOT NULL", "UNIQUE", "CHECK", "FOREIGN KEY", "DEFAULT"])
            self.constraint_type_cb.currentTextChanged.connect(self._on_constraint_type_changed)
            self.local_cols_list = QListWidget()
            self.local_cols_list.setSelectionMode(QListWidget.MultiSelection)
            cols = self.db_manager.get_columns(table) or []
            for c in cols:
                self.local_cols_list.addItem(QListWidgetItem(c))
            self.check_expr_le = QLineEdit()
            self.default_literal_le = QLineEdit()
            self.fk_ref_table_cb = QComboBox()
            try:
                ref_tables = self.db_manager.list_tables() or []
            except Exception:
                ref_tables = []
            self.fk_ref_table_cb.addItems([""] + ref_tables)
            self.fk_ref_col_cb = QComboBox()
            def on_fk_ref_changed(idx):
                rt = self.fk_ref_table_cb.currentText()
                self.fk_ref_col_cb.clear()
                if rt:
                    try:
                        self.fk_ref_col_cb.addItems(self.db_manager.get_columns(rt) or [])
                    except Exception:
                        pass
            self.fk_ref_table_cb.currentIndexChanged.connect(on_fk_ref_changed)

            self.constraint_name_le = QLineEdit()
            self.params_layout.addRow("Тип ограничения:", self.constraint_type_cb)
            self.params_layout.addRow("Локальные столбцы (выберите):", self.local_cols_list)
            self.params_layout.addRow("CHECK expression:", self.check_expr_le)
            self.params_layout.addRow("DEFAULT literal:", self.default_literal_le)
            self.params_layout.addRow("FK: ref table:", self.fk_ref_table_cb)
            self.params_layout.addRow("FK: ref column:", self.fk_ref_col_cb)
            self.params_layout.addRow("Имя ограничения (опционально):", self.constraint_name_le)
            self._on_constraint_type_changed(self.constraint_type_cb.currentText())

        elif op == "Удалить ограничение":
            self.drop_constraint_le = QLineEdit()
            self.params_layout.addRow("Имя ограничения:", self.drop_constraint_le)
            hint_texts = []
            try:
                cols = self.db_manager.get_columns(table) or []
                for c in cols:
                    md = self.db_manager.get_column_metadata(table, c) or {}
                    for u in md.get('unique_constraints', []):
                        hint_texts.append(u.get('name'))
                    for ch in md.get('check_constraints', []):
                        hint_texts.append(ch.get('name'))
                    for fk in md.get('foreign_keys', []):
                        hint_texts.append(fk.get('name'))
            except Exception:
                pass
            if hint_texts:
                self.params_layout.addRow(QLabel("Примеры имён ограничений: " + ", ".join(hint_texts[:10])))

    def _on_constraint_type_changed(self, typ):
        if typ == "NOT NULL":
            self.local_cols_list.setVisible(True)
            self.check_expr_le.setVisible(False)
            self.default_literal_le.setVisible(False)
            self.fk_ref_table_cb.setVisible(False)
            self.fk_ref_col_cb.setVisible(False)
        elif typ == "UNIQUE":
            self.local_cols_list.setVisible(True)
            self.check_expr_le.setVisible(False)
            self.default_literal_le.setVisible(False)
            self.fk_ref_table_cb.setVisible(False)
            self.fk_ref_col_cb.setVisible(False)
        elif typ == "CHECK":
            self.local_cols_list.setVisible(False)
            self.check_expr_le.setVisible(True)
            self.default_literal_le.setVisible(False)
            self.fk_ref_table_cb.setVisible(False)
            self.fk_ref_col_cb.setVisible(False)
        elif typ == "FOREIGN KEY":
            self.local_cols_list.setVisible(True)
            self.check_expr_le.setVisible(False)
            self.default_literal_le.setVisible(False)
            self.fk_ref_table_cb.setVisible(True)
            self.fk_ref_col_cb.setVisible(True)
        elif typ == "DEFAULT":
            self.local_cols_list.setVisible(True)
            self.check_expr_le.setVisible(False)
            self.default_literal_le.setVisible(True)
            self.fk_ref_table_cb.setVisible(False)
            self.fk_ref_col_cb.setVisible(False)

    def on_show_table_metadata(self):
        table = self.table_combo.currentText()
        if not table:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу")
            return
        dlg = TableMetadataDialog(self.db_manager, table, parent=self)
        dlg.exec()

    def on_preview_clicked(self):
        op = self.operation_combo.currentText()
        table = self.table_combo.currentText()
        if not table:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу")
            return
        s = "<пример SQL не сформирован>"
        try:
            if op == "Добавить столбец":
                s = f'ALTER TABLE "{table}" ADD COLUMN "{self.col_name_le.text()}" {self.type_cb.currentText()}'
            elif op == "Удалить столбец":
                s = f'ALTER TABLE "{table}" DROP COLUMN "{self.column_cb.currentText()}" CASCADE'
            elif op == "Переименовать таблицу":
                s = f'ALTER TABLE "{table}" RENAME TO "{self.new_table_le.text()}"'
            elif op == "Переименовать столбец":
                s = f'ALTER TABLE "{table}" RENAME COLUMN "{self.old_col_cb.currentText()}" TO "{self.new_col_le.text()}"'
            elif op == "Изменить тип данных":
                s = f'ALTER TABLE "{table}" ALTER COLUMN "{self.col_cb.currentText()}" TYPE {self.new_type_cb.currentText()} USING "{self.col_cb.currentText()}"::{self.new_type_cb.currentText()}'
            elif op == "Добавить ограничение":
                s = f'Добавление ограничения ({self.constraint_type_cb.currentText()})'
            elif op == "Удалить ограничение":
                s = f'ALTER TABLE "{table}" DROP CONSTRAINT "{self.drop_constraint_le.text()}" CASCADE'
        except Exception:
            s = "Не удалось сформировать пример."
        QMessageBox.information(self, "Пример SQL", s)

    def on_execute_clicked(self):
        op = self.operation_combo.currentText()
        table = self.table_combo.currentText()
        if not table:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу")
            return

        if op == "Добавить столбец":
            col = self.col_name_le.text().strip()
            dtype = self.type_cb.currentText()
            notnull = self.notnull_cb.isChecked()
            default = self.default_le.text().strip() or None
            unique = self.unique_cb.isChecked()
            cname = self.constraint_name_le.text().strip() or None
            ok = False
            try:
                ok = self.db_manager.alter_add_column(table, col, dtype, nullable=not notnull, default=default, unique=unique, constraint_name=cname)
            except Exception as e:
                ok = False
                logging.exception(e)
            if ok:
                QMessageBox.information(self, "Успех", "Колонка добавлена.")
                try:
                    self.db_manager.mark_structure_changed()
                except Exception:
                    pass
                self.load_tables()
                self.update_params_form()
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось добавить колонку. Проверьте логи.")

        elif op == "Удалить столбец":
            col = self.column_cb.currentText()
            ok = self.db_manager.alter_drop_column(table, col, cascade=True)
            if ok:
                QMessageBox.information(self, "Успех", "Колонка удалена.")
                try:
                    self.db_manager.mark_structure_changed()
                except Exception:
                    pass
                self.load_tables()
                self.update_params_form()
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить колонку. Проверьте логи.")

        elif op == "Переименовать таблицу":
            new = self.new_table_le.text().strip()
            ok = self.db_manager.alter_rename_table(table, new)
            if ok:
                QMessageBox.information(self, "Успех", "Таблица переименована.")
                try:
                    self.db_manager.mark_structure_changed()
                except Exception:
                    pass
                self.load_tables()
                self.update_params_form()
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось переименовать таблицу.")

        elif op == "Переименовать столбец":
            old = self.old_col_cb.currentText()
            new = self.new_col_le.text().strip()
            ok = self.db_manager.alter_rename_column(table, old, new)
            if ok:
                QMessageBox.information(self, "Успех", "Столбец переименован.")
                try:
                    self.db_manager.mark_structure_changed()
                except Exception:
                    pass
                self.load_tables()
                self.update_params_form()
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось переименовать столбец.")

        elif op == "Изменить тип данных":
            col = self.col_cb.currentText()
            newt = self.new_type_cb.currentText()
            notnull = self.new_notnull_cb.isChecked()
            default = self.new_default_le.text().strip() or None
            unique = self.new_unique_cb.isChecked()
            ref_table = self.new_fk_table_cb.currentText() if hasattr(self, 'new_fk_table_cb') else ""
            ref_col = self.new_fk_col_cb.currentText() if hasattr(self, 'new_fk_col_cb') else ""
            new_fk = None
            if ref_table and ref_col:
                new_fk = {'ref_table': ref_table, 'ref_columns': [ref_col], 'constraint_name': None}

            try:
                ok, msg = self.db_manager.alter_change_type(table, col, newt,
                                                           new_not_null=notnull if notnull else None,
                                                           new_default=default,
                                                           new_unique=unique if unique else None,
                                                           new_fk=new_fk,
                                                           drop_constraints_first=True)
            except Exception as e:
                ok = False
                msg = str(e)

            if ok:
                QMessageBox.information(self, "Успех", "Тип столбца изменён.")
                try:
                    self.db_manager.mark_structure_changed()
                except Exception:
                    pass
                self.load_tables()
                self.update_params_form()
                self.accept()
                return

            if msg and ("invalid input" in msg.lower() or "cannot cast" in msg.lower() or "invalid input syntax" in msg.lower()):
                res = QMessageBox.question(self, "Ошибка при смене типа",
                                           "При смене типа обнаружены несовместимые значения (например текст в числовом поле). "
                                           "Хотите обнулить (SET NULL) все значения в этой колонке и повторить операцию? (Данные будут потеряны)",
                                           QMessageBox.Yes | QMessageBox.No)
                if res == QMessageBox.Yes:
                    # очистка
                    try:
                        cleared = self.db_manager.clear_column_values(table, col)
                    except Exception:
                        cleared = False
                    if not cleared:
                        QMessageBox.warning(self, "Ошибка", "Не удалось очистить колонку. Операция отменена.")
                        return
                    # повторная попытка
                    try:
                        ok2, msg2 = self.db_manager.alter_change_type(table, col, newt,
                                                                     new_not_null=notnull if notnull else None,
                                                                     new_default=default,
                                                                     new_unique=unique if unique else None,
                                                                     new_fk=new_fk,
                                                                     drop_constraints_first=True)
                    except Exception as e:
                        ok2 = False
                        msg2 = str(e)
                    if ok2:
                        QMessageBox.information(self, "Успех", "Тип столбца изменён после обнуления значений.")
                        try:
                            self.db_manager.mark_structure_changed()
                        except Exception:
                            pass
                        self.load_tables()
                        self.update_params_form()
                        self.accept()
                        return
                    else:
                        QMessageBox.warning(self, "Ошибка", f"Повторная попытка не удалась: {msg2}")
                        return
                else:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось изменить тип: {msg}")
                    return
            else:
                QMessageBox.warning(self, "Ошибка", f"Не удалось изменить тип: {msg}")
                return

        elif op == "Добавить ограничение":
            ctype = self.constraint_type_cb.currentText()
            selected_local = [it.text() for it in self.local_cols_list.selectedItems()]
            cname = self.constraint_name_le.text().strip() or None
            details = {}
            if ctype == "NOT NULL":
                success_all = True
                for lc in selected_local:
                    ok = self.db_manager.alter_add_constraint(table, 'NOT NULL', {'column': lc})
                    success_all = success_all and ok
                if success_all:
                    QMessageBox.information(self, "Успех", "NOT NULL применён к выбранным столбцам.")
                    try:
                        self.db_manager.mark_structure_changed()
                    except Exception:
                        pass
                    self.load_tables()
                    self.update_params_form()
                    self.accept()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось применить NOT NULL для всех выбранных столбцов.")
                return

            elif ctype == "UNIQUE":
                if not selected_local:
                    QMessageBox.warning(self, "Ошибка", "Выберите хотя бы один столбец для UNIQUE.")
                    return
                details = {'columns': selected_local, 'name': cname}
                ok = self.db_manager.alter_add_constraint(table, 'UNIQUE', details)
                if ok:
                    QMessageBox.information(self, "Успех", "UNIQUE добавлен.")
                    try:
                        self.db_manager.mark_structure_changed()
                    except Exception:
                        pass
                    self.load_tables()
                    self.update_params_form()
                    self.accept()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить UNIQUE.")
                return

            elif ctype == "CHECK":
                expr = self.check_expr_le.text().strip()
                if not expr:
                    QMessageBox.warning(self, "Ошибка", "Введите выражение CHECK.")
                    return
                details = {'expr': expr, 'name': cname}
                ok = self.db_manager.alter_add_constraint(table, 'CHECK', details)
                if ok:
                    QMessageBox.information(self, "Успех", "CHECK добавлен.")
                    try:
                        self.db_manager.mark_structure_changed()
                    except Exception:
                        pass
                    self.load_tables()
                    self.update_params_form()
                    self.accept()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить CHECK.")
                return

            elif ctype == "FOREIGN KEY":
                if not selected_local or len(selected_local) != 1:
                    QMessageBox.warning(self, "Ошибка", "Выберите ровно один локальный столбец для FOREIGN KEY.")
                    return
                ref_table = self.fk_ref_table_cb.currentText()
                ref_col = self.fk_ref_col_cb.currentText()
                if not ref_table or not ref_col:
                    QMessageBox.warning(self, "Ошибка", "Выберите референсную таблицу и столбец.")
                    return
                details = {'columns': [selected_local[0]], 'ref_table': ref_table, 'ref_columns': [ref_col], 'name': cname}
                ok = self.db_manager.alter_add_constraint(table, 'FOREIGN KEY', details)
                if ok:
                    QMessageBox.information(self, "Успех", "FOREIGN KEY добавлен.")
                    try:
                        self.db_manager.mark_structure_changed()
                    except Exception:
                        pass
                    self.load_tables()
                    self.update_params_form()
                    self.accept()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось добавить FOREIGN KEY.")
                return

            elif ctype == "DEFAULT":
                if not selected_local or len(selected_local) != 1:
                    QMessageBox.warning(self, "Ошибка", "Выберите ровно один столбец для DEFAULT.")
                    return
                lit = self.default_literal_le.text().strip()
                if lit == "":
                    QMessageBox.warning(self, "Ошибка", "Введите литерал DEFAULT (например 0 или 'text').")
                    return
                details = {'column': selected_local[0], 'default': lit}
                ok = self.db_manager.alter_add_constraint(table, 'DEFAULT', details)
                if ok:
                    QMessageBox.information(self, "Успех", "DEFAULT установлен.")
                    try:
                        self.db_manager.mark_structure_changed()
                    except Exception:
                        pass
                    self.load_tables()
                    self.update_params_form()
                    self.accept()
                else:
                    QMessageBox.warning(self, "Ошибка", "Не удалось установить DEFAULT.")
                return

        elif op == "Удалить ограничение":
            cname = self.drop_constraint_le.text().strip()
            if not cname:
                QMessageBox.warning(self, "Ошибка", "Введите имя ограничения.")
                return
            ok = self.db_manager.alter_drop_constraint(table, cname)
            if ok:
                QMessageBox.information(self, "Успех", "Ограничение удалено.")
                try:
                    self.db_manager.mark_structure_changed()
                except Exception:
                    pass
                self.load_tables()
                self.update_params_form()
                self.accept()
            else:
                QMessageBox.warning(self, "Ошибка", "Не удалось удалить ограничение.")