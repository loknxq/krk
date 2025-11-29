from typing import List, Tuple, Any, Optional, Dict

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QPushButton, QLabel, QTextEdit, QComboBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                               QTabWidget, QWidget, QGroupBox, QInputDialog, QDoubleSpinBox, QCheckBox, QDateEdit,
                               QDateTimeEdit, QTimeEdit, QSpinBox)
from PySide6.QtCore import Qt, QDate, QDateTime, QTime
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
        self.host_input.setText(params.get('host'))
        self.port_input.setText(params.get('port'))
        self.dbname_input.setText(params.get('dbname'))
        self.user_input.setText(params.get('user'))
        self.password_input.setText(params.get('password'))

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

class EditDataDialog(QDialog):

    def __init__(self, db_manager, table_name: str, pk_values: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.current_table = table_name
        self.pk_values = pk_values or {}
        self.setWindowTitle(f"Редактировать запись: {table_name}")
        self.setMinimumSize(500, 420)

        self.field_widgets: Dict[str, Tuple[Any, Dict[str, Any]]] = {}

        self.setup_ui()

        self._load_row_and_build_fields()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_h = QHBoxLayout()
        top_h.addWidget(QLabel("Таблица:"))
        self.table_label = QLabel(self.current_table or "")
        top_h.addWidget(self.table_label)
        top_h.addStretch()
        layout.addLayout(top_h)

        self.form_area = QWidget()
        self.form_layout = QFormLayout(self.form_area)
        layout.addWidget(self.form_area)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить")
        self.save_btn.clicked.connect(self.on_save_clicked)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    def _load_row_and_build_fields(self):
        try:
            cols = self.db_manager.get_columns(self.current_table) or []
        except Exception as e:
            logging.exception("get_columns failed: %s", e)
            cols = []

        row = None
        if self.pk_values:
            pk_items = list(self.pk_values.items())
            where_clauses = []
            params = []
            for k, v in pk_items:
                where_clauses.append(f"{_quote_ident(k)} = %s")
                params.append(v)
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=0"
            sql = f"SELECT * FROM {_quote_ident(self.current_table)} WHERE {where_sql} LIMIT 1"
            try:
                cur = self.db_manager.execute(sql, tuple(params))
                if cur:
                    try:
                        rows = cur.fetchall()
                        if rows:
                            row = rows[0]
                        try:
                            cur.close()
                        except Exception:
                            pass
                    except Exception:
                        row = None
            except Exception:
                logging.exception("Failed to fetch row for editing")


        while self.form_layout.rowCount():
            self.form_layout.removeRow(0)
        self.field_widgets.clear()

        processed_cols = []
        for c in cols:
            if hasattr(c, "name"):
                processed_cols.append(c.name)
            else:
                processed_cols.append(str(c))
        cols = processed_cols

        if not cols:
            self.form_layout.addRow(QLabel("Нет колонок для таблицы или не удалось загрузить метаданные"))
            return


        row_values_by_col = {}
        if row is not None:
            try:
                if len(row) == len(cols):
                    for i, col in enumerate(cols):
                        row_values_by_col[col] = row[i]
                else:
                    for i, col in enumerate(cols):
                        if i < len(row):
                            row_values_by_col[col] = row[i]
            except Exception:
                pass

        for col in cols:
            try:
                meta = self.db_manager.get_column_metadata(self.current_table, col) or {}
            except Exception:
                logging.exception("get_column_metadata failed for %s.%s", self.current_table, col)
                meta = {}

            is_pk = bool(meta.get('is_primary'))

            if is_pk:
                label_text = f"{col} (PK)"
                value = row_values_by_col.get(col, self.pk_values.get(col))
                vstr = "" if value is None else str(value)
                label_widget = QLabel(vstr)
                label_widget.setToolTip(vstr)
                self.form_layout.addRow(QLabel(label_text), label_widget)
                self.field_widgets[col] = (label_widget, meta)
                continue

            data_type = (meta.get('data_type') or "").lower()
            udt = (meta.get('udt_name') or "").lower()
            enum_values = meta.get('enum_values')

            widget = None

            if enum_values and isinstance(enum_values, (list, tuple)) and len(enum_values) > 0:
                cb = QComboBox()
                cb.addItem("")
                for v in enum_values:
                    cb.addItem(str(v))
                widget = cb

            elif data_type in ("integer", "smallint", "bigint") or udt in ("int2", "int4", "int8"):
                sb = QSpinBox()
                sb.setRange(-2147483648, 2147483647)
                sb.setSpecialValueText("")
                sb.setValue(0)
                widget = sb

            elif data_type in ("numeric", "real", "double precision", "decimal") or udt in ("float4", "float8", "numeric"):
                db = QDoubleSpinBox()
                db.setRange(-1e18, 1e18)
                db.setDecimals(6)
                db.setSpecialValueText("")
                db.setValue(0.0)
                widget = db

            elif "bool" in data_type or udt == "bool":
                cb = QCheckBox()
                widget = cb

            elif data_type in ("date",):
                de = QDateEdit()
                de.setCalendarPopup(True)
                de.setDisplayFormat("yyyy-MM-dd")
                de.setDate(QDate.currentDate())
                widget = de

            elif data_type in ("timestamp without time zone", "timestamp with time zone", "timestamp"):
                dte = QDateTimeEdit()
                dte.setCalendarPopup(True)
                dte.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
                dte.setDateTime(QDateTime.currentDateTime())
                widget = dte

            elif data_type in ("time without time zone", "time with time zone", "time"):
                te = QTimeEdit()
                te.setDisplayFormat("HH:mm:ss")
                te.setTime(QTime.currentTime())
                widget = te

            elif "text" in data_type or data_type in ("character varying", "varchar", "character", "char"):
                le = QLineEdit()
                widget = le

            else:
                le = QLineEdit()
                widget = le

            label_parts = [f"{col} ({meta.get('data_type') or meta.get('udt_name') or 'unknown'})"]
            if not meta.get('is_nullable', True):
                label_parts.append("NOT NULL")
            if meta.get('column_default') is not None:
                label_parts.append(f"default: {meta.get('column_default')}")
            u_names = [u.get('name') for u in meta.get('unique_constraints', [])] if meta.get('unique_constraints') else []
            if u_names:
                label_parts.append("UNIQUE")
            if meta.get('check_constraints'):
                label_parts.append("CHECK")
            if meta.get('foreign_keys'):
                label_parts.append("FK")

            label_text = "; ".join(label_parts)
            label_widget = QLabel(label_text)
            label_widget.setToolTip(label_text)

            self.field_widgets[col] = (widget, meta)
            self.form_layout.addRow(label_widget, widget)

            if col in row_values_by_col:
                raw_val = row_values_by_col.get(col)
                try:

                    if raw_val is None:
                        rv = ""
                    else:
                        rv = str(raw_val)
                    self._set_widget_value(widget, rv, meta)
                except Exception:
                    logging.debug("Failed to set widget value for %s", col, exc_info=True)

        hint = QLabel("Примечание: первичные ключи показаны как read-only и используются в WHERE для обновления.")
        hint.setStyleSheet("color: #666; font-size: 9pt;")
        self.form_layout.addRow(hint)


    def _set_widget_value(self, widget: Any, raw_val: str, meta: Dict[str, Any]):
        try:
            if isinstance(widget, QComboBox):
                idx = widget.findText(raw_val)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, QSpinBox):
                try:
                    widget.setValue(int(float(raw_val)))
                except Exception:
                    pass
            elif isinstance(widget, QDoubleSpinBox):
                try:
                    widget.setValue(float(raw_val))
                except Exception:
                    pass
            elif isinstance(widget, QCheckBox):
                v = (str(raw_val).lower() in ("true", "t", "1", "yes"))
                widget.setChecked(v)
            elif isinstance(widget, QDateEdit):
                try:
                    d = QDate.fromString(raw_val[:10], "yyyy-MM-dd")
                    if d.isValid():
                        widget.setDate(d)
                except Exception:
                    pass
            elif isinstance(widget, QDateTimeEdit):
                try:
                    dt = QDateTime.fromString(raw_val.replace("T", " ")[:19], "yyyy-MM-dd HH:mm:ss")
                    if dt.isValid():
                        widget.setDateTime(dt)
                except Exception:
                    pass
            elif isinstance(widget, QTimeEdit):
                try:
                    t = QTime.fromString(raw_val[:8], "HH:mm:ss")
                    if t.isValid():
                        widget.setTime(t)
                except Exception:
                    pass
            elif isinstance(widget, QLineEdit) or isinstance(widget, QTextEdit):
                v = raw_val.strip()
                if v.startswith("'") and v.endswith("'"):
                    v = v[1:-1]
                if isinstance(widget, QLineEdit):
                    widget.setText(v)
                else:
                    widget.setPlainText(v)
        except Exception:
            logging.debug("set default failed for widget", exc_info=True)

    def _get_widget_value(self, widget: Any) -> Optional[Any]:
        if isinstance(widget, QComboBox):
            txt = widget.currentText()
            return txt if txt != "" else None
        if isinstance(widget, QSpinBox):
            try:
                val = widget.value()
                return val
            except Exception:
                return None
        if isinstance(widget, QDoubleSpinBox):
            try:
                return widget.value()
            except Exception:
                return None
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QDateEdit):
            return widget.date().toString("yyyy-MM-dd")
        if isinstance(widget, QDateTimeEdit):
            return widget.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        if isinstance(widget, QTimeEdit):
            return widget.time().toString("HH:mm:ss")
        if isinstance(widget, QLineEdit):
            txt = widget.text().strip()
            return txt if txt != "" else None
        if isinstance(widget, QTextEdit):
            txt = widget.toPlainText().strip()
            return txt if txt != "" else None
        try:
            txt = str(widget.text()).strip()
            return txt if txt != "" else None
        except Exception:
            return None

    def _validate_fields(self) -> Tuple[bool, Optional[str]]:
        table = self.current_table
        for col, (widget, meta) in self.field_widgets.items():
            if meta.get('is_primary'):
                continue
            val = self._get_widget_value(widget)
            if not meta.get('is_nullable', True):
                if val is None:
                    return False, f"Поле '{col}' не может быть NULL (NOT NULL)."

            uniqs = meta.get('unique_constraints') or []
            for uq in uniqs:
                cols = uq.get('columns') or []
                if len(cols) == 1 and cols[0] == col:
                    try:
                        where_parts = [f"{_quote_ident(col)} = %s"]
                        params = [val]
                        exclude_clauses = []
                        for k, v in self.pk_values.items():
                            exclude_clauses.append(f"{_quote_ident(k)} != %s")
                            params.append(v)
                        exclude_sql = " AND ".join(exclude_clauses) if exclude_clauses else "1=1"
                        sql = f"SELECT 1 FROM {_quote_ident(table)} WHERE {where_parts[0]} AND ({exclude_sql}) LIMIT 1"
                        cur = self.db_manager.execute(sql, tuple(params))
                        exists = False
                        if cur:
                            try:
                                r = cur.fetchall()
                                exists = len(r) > 0
                            except Exception:
                                exists = False
                            try:
                                cur.close()
                            except Exception:
                                pass
                        if exists:
                            return False, f"Значение поля '{col}' должно быть уникально, но такое уже есть в таблице."
                    except Exception:
                        logging.exception("unique check failed")
                        pass

            dt = (meta.get('data_type') or '').lower()
            if val is not None and isinstance(widget, QLineEdit):
                if dt in ("integer", "smallint", "bigint", "int4", "int2", "int8"):
                    try:
                        int(val)
                    except Exception:
                        return False, f"Поле '{col}' должно быть целым числом."
                elif dt in ("numeric", "real", "double precision", "decimal", "float4", "float8"):
                    try:
                        float(val)
                    except Exception:
                        return False, f"Поле '{col}' должно быть числом."

        return True, None

    def on_save_clicked(self):
        if not self.current_table:
            QMessageBox.warning(self, "Ошибка", "Не выбрана таблица.")
            return

        ok, msg = self._validate_fields()
        if not ok:
            QMessageBox.warning(self, "Ошибка валидации", msg or "Некорректные данные.")
            return

        set_cols = []
        params = []
        for col, (widget, meta) in self.field_widgets.items():
            if meta.get('is_primary'):
                continue
            v = self._get_widget_value(widget)
            set_cols.append(f"{_quote_ident(col)} = %s")
            params.append(v)

        if not set_cols:
            QMessageBox.information(self, "Нечего обновлять", "Нет редактируемых полей.")
            return

        where_parts = []
        where_params = []
        for k, v in self.pk_values.items():
            where_parts.append(f"{_quote_ident(k)} = %s")
            where_params.append(v)

        sql = f"UPDATE {_quote_ident(self.current_table)} SET {', '.join(set_cols)} WHERE {' AND '.join(where_parts)}"
        all_params = tuple(params) + tuple(where_params)

        try:
            cur = self.db_manager.execute(sql, all_params)
            if cur:
                try:
                    try:
                        if hasattr(self.db_manager, "connection") and getattr(self.db_manager, "connection", None) is not None:
                            try:
                                self.db_manager.connection.commit()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    try:
                        cur.close()
                    except Exception:
                        pass
                except Exception:
                    pass
            QMessageBox.information(self, "Успех", "Запись обновлена.")
            self.accept()
        except Exception as e:
            logging.exception("update failed: %s", e)
            QMessageBox.warning(self, "Ошибка при сохранении", f"Не удалось обновить запись:\n{e}")


class DataViewDialog(QDialog):
    def __init__(self, db_manager, parent=None):

        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Просмотр данных")
        self.setMinimumSize(900, 700)

        self.schema = {}

        self.setup_ui()
        try:
            self.check_structure_changes()
        except Exception:
            pass
        self.load_data()

    def check_structure_changes(self):

        try:
            has_changed = False
            if hasattr(self.db_manager, "has_structure_changed"):
                has_changed = self.db_manager.has_structure_changed()
            if has_changed:
                reply = QMessageBox.question(self, "Обновление структуры",
                                             "Структура базы данных была изменена. Хотите обновить данные?",
                                             QMessageBox.Yes | QMessageBox.No)
                if reply == QMessageBox.Yes:
                    self.refresh_table_structure()
                if hasattr(self.db_manager, "clear_structure_changed"):
                    try:
                        self.db_manager.clear_structure_changed()
                    except Exception:
                        logging.exception("clear_structure_changed failed")
        except Exception:
            logging.exception("check_structure_changes failed")

    def refresh_table_structure(self):

        try:
            if hasattr(self.db_manager, "refresh_connection"):
                try:
                    self.db_manager.refresh_connection()
                except Exception:
                    logging.exception("refresh_connection failed")

            self.load_data()
        except Exception as e:
            logging.exception(f"Ошибка обновления структуры таблиц: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось обновить структуру таблиц: {e}")

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        refresh_structure_btn = QPushButton("Обновить структуру таблиц")
        refresh_structure_btn.setToolTip("Принудительно перезагрузить структуру таблиц")
        refresh_structure_btn.clicked.connect(self.refresh_table_structure)
        refresh_btn = QPushButton("Обновить данные")
        refresh_btn.clicked.connect(self.load_data)

        top_row.addWidget(refresh_structure_btn)
        top_row.addWidget(refresh_btn)
        top_row.addStretch()
        layout.addLayout(top_row)

        # Вкладки с таблицами
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

    # --- Создание вкладки для таблицы ---
    def create_table_tab(self, table_name: str, headers: List[str]) -> QWidget:

        widget = QWidget()
        vlay = QVBoxLayout(widget)

        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel(f"Таблица: {table_name}"))

        edit_btn = QPushButton("Редактировать")
        edit_btn.clicked.connect(lambda: self.open_edit_dialog(table_name))
        header_layout.addWidget(edit_btn)
        header_layout.addStretch()
        vlay.addLayout(header_layout)

        table = QTableWidget(0, len(headers))
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setDefaultSectionSize(28)

        vlay.addWidget(table)

        return widget

    def open_edit_dialog(self, table_name: str):

        cols = self.schema.get(table_name) or []
        if not cols:
            try:
                cols = self.db_manager.get_columns(table_name) or []
            except Exception:
                cols = []

        if not cols:
            QMessageBox.warning(self, "Ошибка", f"Не удалось определить колонки таблицы '{table_name}'")
            return

        pk_columns = []
        try:
            for c in cols:
                try:
                    meta = self.db_manager.get_column_metadata(table_name, c) or {}
                except Exception:
                    meta = {}
                if meta.get('is_primary'):
                    pk_columns.append(c)
        except Exception:
            pk_columns = []

        if not pk_columns:
            for c in cols:
                if c.lower() == 'id':
                    pk_columns = [c]
                    break
        if not pk_columns:
            pk_columns = [cols[0]]

        pk_values = {}
        for pk_col in pk_columns:
            val, ok = QInputDialog.getText(self, "Открыть запись", f"Введите значение для ключа {pk_col}:")
            if not ok:
                return
            pk_values[pk_col] = val

        try:
            where_parts = [f"{_quote_ident(k)} = %s" for k in pk_columns]
            params = tuple(pk_values[k] for k in pk_columns)
            sql = f"SELECT * FROM {_quote_ident(table_name)} WHERE " + " AND ".join(where_parts) + " LIMIT 1"
            cur = None
            try:
                cur = self.db_manager.execute(sql, params)
                if not cur:
                    QMessageBox.warning(self, "Ошибка", "Не удалось выполнить запрос к базе данных.")
                    return
                rows = []
                try:
                    rows = cur.fetchall()
                except Exception:
                    rows = []
                row_data = rows[0] if rows else None
                desc = getattr(cur, "description", None)
                col_names = [d[0] for d in desc] if desc else cols
            finally:
                try:
                    if cur is not None:
                        cur.close()
                except Exception:
                    pass

            if not row_data:
                QMessageBox.information(self, "Не найдено",
                                        f"Запись с {', '.join([f'{k}={pk_values[k]}' for k in pk_columns])} не найдена в таблице '{table_name}'")
                return

            try:
                EditDataDialog
                try:
                    dlg = EditDataDialog(self.db_manager, table_name, pk_values, parent=self)
                    if dlg.exec() == QDialog.Accepted:
                        if hasattr(dlg, "get_action_info"):
                            try:
                                action_type, row_id = dlg.get_action_info()
                                self.handle_table_action(table_name, action_type, row_id)
                            except Exception:
                                self.load_data()
                        else:
                            self.load_data()
                    return
                except Exception:
                    logging.exception("Запуск EditDataDialog завершился ошибкой, fallback к просмотру")
            except NameError:
                pass

        except Exception as e:
            logging.exception(f"Ошибка при открытии записи: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить запись: {e}")

    def handle_table_action(self, table_name: str, action_type: str, row_id):

        try:
            if action_type == 'delete':
                deleted = False
                if hasattr(self.db_manager, "delete_row"):
                    try:
                        deleted = self.db_manager.delete_row(table_name, row_id)
                    except Exception:
                        deleted = False

                if not deleted:
                    cols = self.schema.get(table_name) or self.db_manager.get_columns(table_name) or []
                    if not cols:
                        QMessageBox.warning(self, "Ошибка", "Не удалось определить колонки для удаления.")
                        return
                    pk = next((c for c in cols if c.lower() == 'id'), cols[0])
                    try:
                        cur = self.db_manager.execute(f"DELETE FROM {table_name} WHERE {pk} = %s", (row_id,))
                        try:
                            if cur is not None:
                                cur.close()
                        except Exception:
                            pass
                        deleted = True
                    except Exception:
                        deleted = False

                if deleted:
                    QMessageBox.information(self, "Успех", f"Строка {row_id} удалена из таблицы '{table_name}'")
                    self.load_data()
                else:
                    QMessageBox.warning(self, "Ошибка", f"Не удалось удалить строку {row_id} из таблицы '{table_name}'")

            elif action_type == 'edit':
                self.load_data()

        except Exception as e:
            logging.exception(f"Ошибка обработки действия: {e}")
            QMessageBox.warning(self, "Ошибка", f"Ошибка: {e}")

    def load_data(self):

        try:
            try:
                tables = self.db_manager.list_tables() or []
            except Exception:
                tables = []

            self.tabs.clear()
            self.schema = {}

            for table_name in tables:
                # получаем колонки
                try:
                    cols = self.db_manager.get_columns(table_name) or []
                except Exception:
                    # попытка через get_table()
                    try:
                        tobj = self.db_manager.get_table(table_name)
                        cols = [c.name for c in getattr(tobj, "columns", [])] if tobj is not None else []
                    except Exception:
                        cols = []

                # если нет колонок — пропустить
                if not cols:
                    cols = []

                # сохраняем в схеме
                self.schema[table_name] = cols

                # создаём вкладку и таблицу
                tab = self.create_table_tab(table_name, cols)
                self.tabs.addTab(tab, table_name)

                # находим QTableWidget внутри вкладки и наполняем данными
                table_widget = tab.findChild(QTableWidget)
                if table_widget is None:
                    continue

                # получить данные
                rows = []
                try:
                    cur = self.db_manager.execute(f"SELECT * FROM {table_name}")
                    if cur:
                        try:
                            rows = cur.fetchall()
                            desc = getattr(cur, "description", None)
                            if desc and (not cols):
                                cols = [d[0] for d in desc]
                                # обновим заголовки в виджете
                                table_widget.setColumnCount(len(cols))
                                table_widget.setHorizontalHeaderLabels(cols)
                                self.schema[table_name] = cols
                        except Exception:
                            rows = []
                        finally:
                            try:
                                cur.close()
                            except Exception:
                                pass
                except Exception:
                    rows = []

                # наполнение таблицы
                self.load_table_data(table_widget, rows, cols)

        except Exception as e:
            logging.exception(f"Ошибка загрузки данных: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные: {e}")

    def load_table_data(self, table: QTableWidget, data: List[Tuple], columns: List[str]):

        table.verticalHeader().setDefaultSectionSize(28)
        if not data:
            table.setRowCount(1)
            if table.columnCount() == 0:
                table.setColumnCount(max(1, len(columns)))
            no_item = QTableWidgetItem("Нет данных")
            no_item.setFlags(no_item.flags() & ~Qt.ItemIsEditable)
            table.setItem(0, 0, no_item)
            return

        if table.columnCount() != len(columns):
            table.setColumnCount(len(columns))
            table.setHorizontalHeaderLabels(columns)

        table.setRowCount(len(data))
        for row_idx, row in enumerate(data):
            for col_idx in range(len(columns)):
                val = row[col_idx] if col_idx < len(row) else None
                item = QTableWidgetItem(str(val) if val is not None else "")
                item.setFlags(item.flags() & ~Qt.ItemIsEditable)
                table.setItem(row_idx, col_idx, item)

def _quote_ident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

class AddDataDialog(QDialog):

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Добавить запись")
        self.setMinimumSize(500, 400)

        self.field_widgets: Dict[str, Tuple[Any, Dict[str, Any]]] = {}
        self.current_table: Optional[str] = None

        self.setup_ui()
        self.load_tables()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form_top = QHBoxLayout()
        form_top.addWidget(QLabel("Таблица:"))
        self.table_cb = QComboBox()
        self.table_cb.currentTextChanged.connect(self.on_table_changed)
        form_top.addWidget(self.table_cb)
        layout.addLayout(form_top)

        self.form_area = QWidget()
        self.form_layout = QFormLayout(self.form_area)
        layout.addWidget(self.form_area)

        btn_row = QHBoxLayout()
        self.add_btn = QPushButton("Добавить")
        self.add_btn.clicked.connect(self.on_add_clicked)
        self.cancel_btn = QPushButton("Отмена")
        self.cancel_btn.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(self.add_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

    def load_tables(self):
        self.table_cb.clear()
        try:
            tables = self.db_manager.list_tables() or []
        except Exception as e:
            logging.exception("load_tables failed: %s", e)
            tables = []
        for t in sorted(tables):
            self.table_cb.addItem(t)
        if self.table_cb.count():
            self.table_cb.setCurrentIndex(0)

    def on_table_changed(self, table_name: str):
        self.current_table = table_name
        self.build_fields_for_table(table_name)

    def build_fields_for_table(self, table_name: str):
        while self.form_layout.rowCount():
            self.form_layout.removeRow(0)
        self.field_widgets.clear()

        if not table_name:
            return

        try:
            cols = self.db_manager.get_columns(table_name) or []
        except Exception as e:
            logging.exception("get_columns failed: %s", e)
            cols = []

        for col in cols:
            try:
                meta = self.db_manager.get_column_metadata(table_name, col) or {}
            except Exception:
                logging.exception("get_column_metadata failed for %s.%s", table_name, col)
                meta = {}

            if meta.get('is_primary'):
                continue

            data_type = (meta.get('data_type') or "").lower()
            udt = (meta.get('udt_name') or "").lower()
            enum_values = meta.get('enum_values')  

            widget = None

            if enum_values and isinstance(enum_values, (list, tuple)) and len(enum_values) > 0:
                cb = QComboBox()
                cb.addItem("") 
                for v in enum_values:
                    cb.addItem(str(v))
                widget = cb

            elif data_type in ("integer", "smallint", "bigint") or udt in ("int2", "int4", "int8"):
                sb = QSpinBox()
                sb.setRange(-2147483648, 2147483647)
                sb.setSpecialValueText("") 
                sb.setValue(0)
                widget = sb

            elif data_type in ("numeric", "real", "double precision", "decimal") or udt in ("float4", "float8", "numeric"):
                db = QDoubleSpinBox()
                db.setRange(-1e18, 1e18)
                db.setDecimals(6)
                db.setSpecialValueText("")
                db.setValue(0.0)
                widget = db

            elif "bool" in data_type or udt == "bool":
                cb = QCheckBox()
                widget = cb

            elif data_type in ("date",):
                de = QDateEdit()
                de.setCalendarPopup(True)
                de.setDisplayFormat("yyyy-MM-dd")
                de.setDate(QDate.currentDate())
                widget = de

            elif data_type in ("timestamp without time zone", "timestamp with time zone", "timestamp"):
                dte = QDateTimeEdit()
                dte.setCalendarPopup(True)
                dte.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
                dte.setDateTime(QDateTime.currentDateTime())
                widget = dte

            elif data_type in ("time without time zone", "time with time zone", "time"):
                te = QTimeEdit()
                te.setDisplayFormat("HH:mm:ss")
                te.setTime(QTime.currentTime())
                widget = te

            elif "text" in data_type or data_type in ("character varying", "varchar", "character", "char"):
                # if large text, consider QTextEdit
                le = QLineEdit()
                widget = le

            else:
                le = QLineEdit()
                widget = le

            label_parts = [f"{col} ({meta.get('data_type') or meta.get('udt_name') or 'unknown'})"]
            if not meta.get('is_nullable', True):
                label_parts.append("NOT NULL")
            if meta.get('column_default') is not None:
                label_parts.append(f"default: {meta.get('column_default')}")
            u_names = [u.get('name') for u in meta.get('unique_constraints', [])] if meta.get('unique_constraints') else []
            if u_names:
                label_parts.append("UNIQUE")
            if meta.get('check_constraints'):
                label_parts.append("CHECK")
            if meta.get('foreign_keys'):
                label_parts.append("FK")

            label_text = "; ".join(label_parts)
            label_widget = QLabel(label_text)
            label_widget.setToolTip(label_text)


            self.field_widgets[col] = (widget, meta)

            self.form_layout.addRow(label_widget, widget)

            default_val = meta.get('column_default')
            if default_val is not None and default_val != "":
                try:
                    dv = str(default_val)
                    if "nextval" in dv.lower():
                        pass
                    else:
                        self._set_widget_value(widget, dv, meta)
                except Exception:
                    pass

        hint = QLabel("Примечание: первичные ключи (PK) автоматически обрабатываются базой; они не отображаются здесь.")
        hint.setStyleSheet("color: #666; font-size: 9pt;")
        self.form_layout.addRow(hint)

    def _set_widget_value(self, widget: Any, raw_val: str, meta: Dict[str, Any]):
        try:
            if isinstance(widget, QComboBox):
                idx = widget.findText(raw_val)
                if idx >= 0:
                    widget.setCurrentIndex(idx)
            elif isinstance(widget, QSpinBox):
                try:
                    widget.setValue(int(float(raw_val)))
                except Exception:
                    pass
            elif isinstance(widget, QDoubleSpinBox):
                try:
                    widget.setValue(float(raw_val))
                except Exception:
                    pass
            elif isinstance(widget, QCheckBox):
                v = raw_val.lower() in ("true", "t", "1", "yes")
                widget.setChecked(v)
            elif isinstance(widget, QDateEdit):
                try:
                    d = QDate.fromString(raw_val[:10], "yyyy-MM-dd")
                    if d.isValid():
                        widget.setDate(d)
                except Exception:
                    pass
            elif isinstance(widget, QDateTimeEdit):
                try:
                    dt = QDateTime.fromString(raw_val.replace("T", " ")[:19], "yyyy-MM-dd HH:mm:ss")
                    if dt.isValid():
                        widget.setDateTime(dt)
                except Exception:
                    pass
            elif isinstance(widget, QTimeEdit):
                try:
                    t = QTime.fromString(raw_val[:8], "HH:mm:ss")
                    if t.isValid():
                        widget.setTime(t)
                except Exception:
                    pass
            elif isinstance(widget, QLineEdit) or isinstance(widget, QTextEdit):
                v = raw_val.strip()
                if v.startswith("'") and v.endswith("'"):
                    v = v[1:-1]
                if isinstance(widget, QLineEdit):
                    widget.setText(v)
                else:
                    widget.setPlainText(v)
        except Exception:
            logging.debug("set default failed for widget", exc_info=True)

    def _get_widget_value(self, widget: Any) -> Optional[Any]:
        if isinstance(widget, QComboBox):
            txt = widget.currentText()
            return txt if txt != "" else None
        if isinstance(widget, QSpinBox):

            try:
                val = widget.value()
                return val
            except Exception:
                return None
        if isinstance(widget, QDoubleSpinBox):
            try:
                return widget.value()
            except Exception:
                return None
        if isinstance(widget, QCheckBox):
            return widget.isChecked()
        if isinstance(widget, QDateEdit):
            return widget.date().toString("yyyy-MM-dd")
        if isinstance(widget, QDateTimeEdit):
            return widget.dateTime().toString("yyyy-MM-dd HH:mm:ss")
        if isinstance(widget, QTimeEdit):
            return widget.time().toString("HH:mm:ss")
        if isinstance(widget, QLineEdit):
            txt = widget.text().strip()
            return txt if txt != "" else None
        if isinstance(widget, QTextEdit):
            txt = widget.toPlainText().strip()
            return txt if txt != "" else None
        # fallback
        try:
            txt = str(widget.text()).strip()
            return txt if txt != "" else None
        except Exception:
            return None

    def _validate_fields(self) -> Tuple[bool, Optional[str]]:

        table = self.current_table
        for col, (widget, meta) in self.field_widgets.items():
            val = self._get_widget_value(widget)
            if not meta.get('is_nullable', True):
                if val is None:
                    return False, f"Поле '{col}' не может быть NULL (NOT NULL)."

            uniqs = meta.get('unique_constraints') or []
            for uq in uniqs:
                cols = uq.get('columns') or []
                if len(cols) == 1 and cols[0] == col:
                    try:
                        cur = self.db_manager.execute(
                            f"SELECT 1 FROM {_quote_ident(table)} WHERE {_quote_ident(col)} = %s LIMIT 1",
                            (val,)
                        )
                        exists = False
                        if cur:
                            try:
                                r = cur.fetchall()
                                exists = len(r) > 0
                            except Exception:
                                exists = False
                            try:
                                cur.close()
                            except Exception:
                                pass
                        if exists:
                            return False, f"Значение поля '{col}' должно быть уникально, но такое уже есть в таблице."
                    except Exception as e:
                        logging.exception("unique check failed: %s", e)
                        pass


            dt = (meta.get('data_type') or '').lower()
            if val is not None and isinstance(widget, QLineEdit):
                if dt in ("integer", "smallint", "bigint", "int4", "int2", "int8"):
                    try:
                        int(val)
                    except Exception:
                        return False, f"Поле '{col}' должно быть целым числом."
                elif dt in ("numeric", "real", "double precision", "decimal", "float4", "float8"):
                    try:
                        float(val)
                    except Exception:
                        return False, f"Поле '{col}' должно быть числом."

        return True, None

    def on_add_clicked(self):

        if not self.current_table:
            QMessageBox.warning(self, "Ошибка", "Не выбрана таблица.")
            return

        ok, msg = self._validate_fields()
        if not ok:
            QMessageBox.warning(self, "Ошибка валидации", msg or "Некорректные данные.")
            return

        cols = []
        vals = []
        params = []
        for col, (widget, meta) in self.field_widgets.items():
            v = self._get_widget_value(widget)
            if v is None:
                continue
            cols.append(col)
            vals.append("%s")
            params.append(v)

        if not cols:
            sql = f"INSERT INTO {_quote_ident(self.current_table)} DEFAULT VALUES"
        else:
            col_list = ", ".join([_quote_ident(c) for c in cols])
            placeholders = ", ".join(vals)
            sql = f"INSERT INTO {_quote_ident(self.current_table)} ({col_list}) VALUES ({placeholders})"

        try:
            cur = self.db_manager.execute(sql, tuple(params) if params else None)
            if cur:
                try:
                    try:
                        if hasattr(self.db_manager, "connection") and getattr(self.db_manager, "connection", None) is not None:
                            try:
                                self.db_manager.connection.commit()
                            except Exception:
                                pass
                    except Exception:
                        pass
                    cur.close()
                except Exception:
                    pass
            QMessageBox.information(self, "Успех", "Запись добавлена.")
            self.accept()
        except Exception as e:
            logging.exception("insert failed: %s", e)
            err = str(e)
            QMessageBox.warning(self, "Ошибка при добавлении", f"Не удалось добавить запись:\n{err}")

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
        self.recreate_btn = QPushButton("3 таблицы")

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