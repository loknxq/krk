from typing import List, Tuple, Any, Optional, Dict

from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
                               QLineEdit, QPushButton, QLabel, QTextEdit, QComboBox,
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                               QTabWidget, QWidget, QGroupBox, QInputDialog, QDoubleSpinBox, QCheckBox, QDateEdit,
                               QDateTimeEdit, QTimeEdit, QSpinBox, QListWidget)
from PySide6.QtCore import Qt, QDate, QDateTime, QTime
import logging

from dialogs import _quote_ident


class EnumCreateDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать ENUM тип")
        self.setMinimumWidth(420)
        self.result_name = ""
        self.result_values: List[str] = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_le = QLineEdit()
        self.name_le.setPlaceholderText("schema.my_enum или my_enum (если schema опущена)")
        form.addRow("Имя типа:", self.name_le)
        self.values_te = QTextEdit()
        self.values_te.setPlaceholderText("Каждое значение с новой строки, например:\nactive\ninactive\npending")
        form.addRow("Значения (по одной на строку):", self.values_te)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        ok = QPushButton("Создать")
        cancel = QPushButton("Отмена")
        ok.clicked.connect(self.on_ok)
        cancel.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(ok)
        btn_row.addWidget(cancel)
        layout.addLayout(btn_row)

    def on_ok(self):
        name = self.name_le.text().strip()
        vals = [v.strip() for v in self.values_te.toPlainText().splitlines() if v.strip()]
        if not name:
            QMessageBox.warning(self, "Ошибка", "Укажите имя типа.")
            return
        if not vals:
            QMessageBox.warning(self, "Ошибка", "Укажите хотя бы одно значение для ENUM.")
            return
        self.result_name = name
        self.result_values = vals
        self.accept()


class CompositeCreateDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Создать составной тип (COMPOSITE)")
        self.setMinimumWidth(480)
        self.result_name = ""
        self.result_fields: List[Tuple[str, str]] = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()
        self.name_le = QLineEdit()
        self.name_le.setPlaceholderText("schema.my_type или my_type")
        form.addRow("Имя типа:", self.name_le)
        self.fields_te = QTextEdit()
        self.fields_te.setPlaceholderText("Поля по одной на строку в формате: name type\nПример:\nfirst_name text\nage integer")
        form.addRow("Поля (name type):", self.fields_te)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        ok = QPushButton("Создать")
        cancel = QPushButton("Отмена")
        ok.clicked.connect(self.on_ok)
        cancel.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(ok)
        btn_row.addWidget(cancel)
        layout.addLayout(btn_row)

    def on_ok(self):
        name = self.name_le.text().strip()
        lines = [l.strip() for l in self.fields_te.toPlainText().splitlines() if l.strip()]
        if not name:
            QMessageBox.warning(self, "Ошибка", "Укажите имя типа.")
            return
        if not lines:
            QMessageBox.warning(self, "Ошибка", "Укажите хотя бы одно поле для типа.")
            return
        fields: List[Tuple[str, str]] = []
        for ln in lines:
            parts = ln.split()
            if len(parts) < 2:
                QMessageBox.warning(self, "Ошибка", f"Неверный формат поля: '{ln}'. Ожидается 'name type'.")
                return
            col = parts[0]
            typ = " ".join(parts[1:])
            fields.append((col, typ))
        self.result_name = name
        self.result_fields = fields
        self.accept()


class ApplyTypeDialog(QDialog):

    def __init__(self, db_manager, type_qname: str, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.type_qname = type_qname
        self.setWindowTitle("Применить тип к столбцу")
        self.setMinimumWidth(480)
        self.result = None
        self.setup_ui()
        self.load_tables()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        form = QFormLayout()
        self.table_cb = QComboBox()
        self.table_cb.currentIndexChanged.connect(self.on_table_changed)
        form.addRow("Таблица:", self.table_cb)

        self.column_cb = QComboBox()
        form.addRow("Столбец:", self.column_cb)

        layout.addLayout(form)

        btn_row = QHBoxLayout()
        add_col_btn = QPushButton("Добавить столбец")
        add_col_btn.clicked.connect(self.on_add_column)
        ok_btn = QPushButton("Применить")
        ok_btn.clicked.connect(self.on_ok)
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(add_col_btn)
        btn_row.addStretch()
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self.warn_label = QLabel("")
        self.warn_label.setWordWrap(True)
        layout.addWidget(self.warn_label)

        self.update_warning()

    def load_tables(self):
        self.table_cb.clear()
        try:
            tables = self.db_manager.list_tables() or []
        except Exception:
            tables = []
        for t in sorted(tables):
            self.table_cb.addItem(t)
        if self.table_cb.count():
            self.table_cb.setCurrentIndex(0)

    def on_table_changed(self, idx):
        tbl = self.table_cb.currentText()
        self.column_cb.clear()
        if not tbl:
            return
        try:
            cols = self.db_manager.get_columns(tbl) or []
        except Exception:
            cols = []
        for c in cols:
            self.column_cb.addItem(c)
        self.update_warning()

    def update_warning(self):
        if self.type_qname:
            self.warn_label.setText(
                "Внимание: если вы примените этот тип к выбранному столбцу, все данные в этом столбце будут стерты."
            )
        else:
            self.warn_label.setText("")

    def on_add_column(self):
        tbl = self.table_cb.currentText()
        if not tbl:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите таблицу.")
            return
        name, ok = QInputDialog.getText(self, "Добавить столбец", "Имя нового столбца:")
        if not ok or not name:
            return
        try:
            dq = self.type_qname
            try:
                schema_part, type_part = dq.split(".", 1)
                q_schema = _quote_ident(schema_part)
                q_type = _quote_ident(type_part)
                type_ref = f"{q_schema}.{q_type}"
            except Exception:
                try:
                    type_ref = _quote_ident(dq)
                except Exception:
                    type_ref = dq
            sql = f"ALTER TABLE {_quote_ident(tbl)} ADD COLUMN {_quote_ident(name)} {type_ref}"
            self.db_manager.execute(sql)
            try:
                if hasattr(self.db_manager, "connection") and getattr(self.db_manager, "connection", None) is not None:
                    try:
                        self.db_manager.connection.commit()
                    except Exception:
                        pass
            except Exception:
                pass
            QMessageBox.information(self, "Успех", f"Столбец {name} добавлен в таблицу {tbl} с типом {self.type_qname}.")
            try:
                cols = self.db_manager.get_columns(tbl) or []
            except Exception:
                cols = []
            self.column_cb.clear()
            for c in cols:
                self.column_cb.addItem(c)
            idx = self.column_cb.findText(name)
            if idx >= 0:
                self.column_cb.setCurrentIndex(idx)
        except Exception as e:
            logging.exception("add column failed")
            QMessageBox.warning(self, "Ошибка", f"Не удалось добавить столбец:\n{e}")

    def on_ok(self):
        tbl = self.table_cb.currentText()
        col = self.column_cb.currentText()
        if not tbl or not col:
            QMessageBox.warning(self, "Ошибка", "Выберите таблицу и столбец.")
            return
        self.result = {'table': tbl, 'column': col, 'is_new': False}
        self.accept()

    def get_result(self):
        return self.result


class UserTypesDialog(QDialog):

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db_manager = db_manager
        self.setWindowTitle("Пользовательские типы")
        self.resize(640, 420)
        self.setup_ui()
        self.load_types()

    def setup_ui(self):
        main_l = QVBoxLayout(self)

        kind_row = QHBoxLayout()
        kind_row.addWidget(QLabel("Категория:"))
        self.kind_cb = QComboBox()
        self.kind_cb.addItems(["Enum", "Composite"])
        self.kind_cb.currentIndexChanged.connect(self.load_types)
        kind_row.addWidget(self.kind_cb)
        kind_row.addStretch()
        main_l.addLayout(kind_row)

        self.types_list = QListWidget()
        self.types_list.setMinimumHeight(160)
        self.types_list.itemSelectionChanged.connect(self.on_selection_changed)
        main_l.addWidget(self.types_list)

        bottom_box = QGroupBox("Описание и операции")
        bottom_l = QVBoxLayout(bottom_box)

        self.detail_te = QTextEdit()
        self.detail_te.setReadOnly(True)
        self.detail_te.setMinimumHeight(140)
        bottom_l.addWidget(self.detail_te)

        ops_row = QHBoxLayout()
        self.create_btn = QPushButton("Создать")
        self.view_btn = QPushButton("Просмотр")
        self.delete_btn = QPushButton("Удалить")
        # заменяем Refresh на Apply
        self.apply_btn = QPushButton("Применить")
        ops_row.addWidget(self.create_btn)
        ops_row.addWidget(self.view_btn)
        ops_row.addWidget(self.delete_btn)
        ops_row.addStretch()
        ops_row.addWidget(self.apply_btn)
        bottom_l.addLayout(ops_row)

        main_l.addWidget(bottom_box)

        self.create_btn.clicked.connect(self.on_create_clicked)
        self.view_btn.clicked.connect(self.on_view_clicked)
        self.delete_btn.clicked.connect(self.on_delete_clicked)
        self.apply_btn.clicked.connect(self.on_apply_clicked)

        self.view_btn.setEnabled(False)
        self.delete_btn.setEnabled(False)
        self.apply_btn.setEnabled(False)

    def _quote_ident_local(self, name: str) -> str:
        try:
            return _quote_ident(name)
        except Exception:
            return '"' + str(name).replace('"', '""') + '"'

    def _split_schema_name(self, qualified: str) -> Tuple[str, str]:
        if '.' in qualified:
            parts = qualified.split('.', 1)
            return parts[0], parts[1]
        else:
            return 'public', qualified

    def load_types(self):
        self.types_list.clear()
        self.detail_te.clear()
        kind = self.kind_cb.currentText()
        try:
            if kind == "Enum":
                items = self._get_enum_types()
            else:
                items = self._get_composite_types()
        except Exception:
            items = []
        for it in items:
            self.types_list.addItem(it)

    def on_selection_changed(self):
        sel = self.types_list.selectedItems()
        ok = len(sel) == 1
        self.view_btn.setEnabled(ok)
        self.delete_btn.setEnabled(ok)
        self.apply_btn.setEnabled(ok)
        if ok:
            self.detail_te.setPlainText(f"Выбран: {sel[0].text()}\n(Нажмите 'Просмотр' для подробностей)")
        else:
            self.detail_te.clear()

    def _get_enum_types(self) -> List[str]:
        try:
            sql = ("SELECT n.nspname || '.' || t.typname AS qname "
                   "FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid "
                   "WHERE t.typtype = 'e' "
                   "ORDER BY qname")
            cur = self.db_manager.execute(sql)
            if not cur:
                return []
            try:
                rows = cur.fetchall()
                return [r[0] for r in rows]
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
        except Exception:
            try:
                builtin = {'int2','int4','int8','float4','float8','numeric','varchar','text','bool','date','timestamp','time','json','jsonb'}
                sql = ("SELECT DISTINCT udt_name FROM information_schema.columns WHERE udt_name IS NOT NULL")
                cur = self.db_manager.execute(sql)
                if not cur:
                    return []
                try:
                    rows = cur.fetchall()
                    names = [r[0] for r in rows if r[0] and r[0] not in builtin]
                    return sorted(names)
                finally:
                    try:
                        cur.close()
                    except Exception:
                        pass
            except Exception:
                return []

    def _get_composite_types(self) -> List[str]:
        try:
            sql = ("SELECT n.nspname || '.' || t.typname AS qname "
                   "FROM pg_type t JOIN pg_namespace n ON t.typnamespace = n.oid "
                   "WHERE t.typtype = 'c' "
                   "  AND n.nspname NOT LIKE 'pg_%' AND n.nspname != 'information_schema' "
                   "ORDER BY qname")
            cur = self.db_manager.execute(sql)
            if not cur:
                return []
            try:
                rows = cur.fetchall()
                return [r[0] for r in rows]
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
        except Exception:
            try:
                sql = "SELECT DISTINCT udt_name FROM information_schema.columns WHERE udt_name IS NOT NULL"
                cur = self.db_manager.execute(sql)
                if not cur:
                    return []
                try:
                    rows = cur.fetchall()
                    names = sorted(set(r[0] for r in rows if r[0] and not str(r[0]).startswith('pg_') and r[0] != 'information_schema'))
                    return names
                finally:
                    try:
                        cur.close()
                    except Exception:
                        pass
            except Exception:
                return []

    def on_create_clicked(self):
        kind = self.kind_cb.currentText()
        if kind == "Enum":
            dlg = EnumCreateDialog(self)
            if dlg.exec():
                self._create_enum(dlg.result_name, dlg.result_values)
        else:
            dlg = CompositeCreateDialog(self)
            if dlg.exec():
                self._create_composite(dlg.result_name, dlg.result_fields)

    def on_view_clicked(self):
        sel = self.types_list.selectedItems()
        if not sel:
            return
        qname = sel[0].text()
        kind = self.kind_cb.currentText()
        try:
            if kind == "Enum":
                txt = self._describe_enum(qname)
            else:
                txt = self._describe_composite(qname)
            self.detail_te.setPlainText(txt)
        except Exception as e:
            logging.exception("describe failed")
            QMessageBox.warning(self, "Ошибка", f"Не удалось получить описание типа:\n{e}")

    def on_delete_clicked(self):
        sel = self.types_list.selectedItems()
        if not sel:
            return
        qualified = sel[0].text()
        schema, name = self._split_schema_name(qualified)

        try:
            sql = ("SELECT table_schema, table_name, column_name FROM information_schema.columns "
                   "WHERE udt_name = %s")
            cur = self.db_manager.execute(sql, (name,))
            used = []
            if cur:
                try:
                    rows = cur.fetchall()
                    for r in rows:
                        used.append(f"{r[0]}.{r[1]}.{r[2]}")
                finally:
                    try:
                        cur.close()
                    except Exception:
                        pass
            if used:
                QMessageBox.warning(self, "Нельзя удалить",
                                    f"Тип {qualified} используется в следующих столбцах:\n" + "\n".join(used))
                return
        except Exception:
            pass

        reply = QMessageBox.question(self, "Удалить тип",
                                     f"Вы уверены, что хотите удалить тип {qualified}?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply != QMessageBox.Yes:
            return

        try:
            q_schema = self._quote_ident_local(schema)
            q_name = self._quote_ident_local(name)
            sql = f"DROP TYPE {q_schema}.{q_name}"
            cur = self.db_manager.execute(sql)
            try:
                if hasattr(self.db_manager, "connection") and getattr(self.db_manager, "connection", None) is not None:
                    try:
                        self.db_manager.connection.commit()
                    except Exception:
                        pass
            except Exception:
                pass
            QMessageBox.information(self, "Успех", f"Тип {qualified} удалён.")
            self.load_types()
        except Exception as e:
            logging.exception("drop type failed")
            QMessageBox.warning(self, "Ошибка удаления", f"Не удалось удалить тип {qualified}:\n{e}")

    def _create_enum(self, qualified_name: str, values: List[str]):
        schema, name = self._split_schema_name(qualified_name)
        q_schema = self._quote_ident_local(schema)
        q_name = self._quote_ident_local(name)
        try:
            vals_sql = ", ".join("'" + v.replace("'", "''") + "'" for v in values)
            sql = f"CREATE TYPE {q_schema}.{q_name} AS ENUM ({vals_sql})"
            self.db_manager.execute(sql)
            try:
                if hasattr(self.db_manager, "connection") and getattr(self.db_manager, "connection", None) is not None:
                    try:
                        self.db_manager.connection.commit()
                    except Exception:
                        pass
            except Exception:
                pass
            QMessageBox.information(self, "Успех", f"ENUM тип {schema}.{name} создан.")
            self.load_types()
        except Exception as e:
            logging.exception("create enum failed")
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать ENUM тип:\n{e}")

    def _create_composite(self, qualified_name: str, fields: List[Tuple[str, str]]):
        schema, name = self._split_schema_name(qualified_name)
        q_schema = self._quote_ident_local(schema)
        q_name = self._quote_ident_local(name)
        try:
            fields_sql = ", ".join(f"{self._quote_ident_local(col)} {typ}" for col, typ in fields)
            sql = f"CREATE TYPE {q_schema}.{q_name} AS ({fields_sql})"
            self.db_manager.execute(sql)
            try:
                if hasattr(self.db_manager, "connection") and getattr(self.db_manager, "connection", None) is not None:
                    try:
                        self.db_manager.connection.commit()
                    except Exception:
                        pass
            except Exception:
                pass
            QMessageBox.information(self, "Успех", f"COMPOSITE тип {schema}.{name} создан.")
            self.load_types()
        except Exception as e:
            logging.exception("create composite failed")
            QMessageBox.warning(self, "Ошибка", f"Не удалось создать составной тип:\n{e}")

    def _describe_enum(self, qualified_name: str) -> str:
        schema, name = self._split_schema_name(qualified_name)
        try:
            sql = ("SELECT e.enumlabel FROM pg_enum e "
                   "JOIN pg_type t ON e.enumtypid = t.oid "
                   "JOIN pg_namespace n ON t.typnamespace = n.oid "
                   "WHERE n.nspname = %s AND t.typname = %s ORDER BY e.enumsortorder")
            cur = self.db_manager.execute(sql, (schema, name))
            if not cur:
                return f"Не удалось получить значения для {qualified_name}"
            try:
                rows = cur.fetchall()
                vals = [r[0] for r in rows]
                return f"ENUM {qualified_name}:\n" + "\n".join(f"- {v}" for v in vals)
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
        except Exception:
            try:
                sql = ("SELECT table_schema, table_name, column_name FROM information_schema.columns "
                       "WHERE udt_name = %s")
                cur = self.db_manager.execute(sql, (name,))
                if cur:
                    try:
                        rows = cur.fetchall()
                        if not rows:
                            return f"ENUM {qualified_name}: отсутствуют дополнительные метаданные."
                        out = [f"Используется в столбцах:"]
                        for r in rows:
                            out.append(f"- {r[0]}.{r[1]}.{r[2]}")
                        return "\n".join(out)
                    finally:
                        try:
                            cur.close()
                        except Exception:
                            pass
                return f"ENUM {qualified_name}: подробности недоступны."
            except Exception:
                return f"Описание для {qualified_name} недоступно для этой СУБД."

    def _describe_composite(self, qualified_name: str) -> str:
        schema, name = self._split_schema_name(qualified_name)
        try:
            sql = ("SELECT a.attname, format_type(a.atttypid, a.atttypmod) AS typ "
                   "FROM pg_attribute a "
                   "JOIN pg_class c ON a.attrelid = c.oid "
                   "JOIN pg_type t ON c.oid = t.typrelid "
                   "JOIN pg_namespace n ON t.typnamespace = n.oid "
                   "WHERE n.nspname = %s AND t.typname = %s AND a.attnum > 0 AND NOT a.attisdropped "
                   "ORDER BY a.attnum")
            cur = self.db_manager.execute(sql, (schema, name))
            if not cur:
                return f"Не удалось получить поля для {qualified_name}"
            try:
                rows = cur.fetchall()
                out = [f"COMPOSITE {qualified_name}:"]
                for r in rows:
                    out.append(f"- {r[0]} : {r[1]}")
                return "\n".join(out)
            finally:
                try:
                    cur.close()
                except Exception:
                    pass
        except Exception:
            return f"Описание для {qualified_name} недоступно для этой СУБД."

    def on_apply_clicked(self):
        sel = self.types_list.selectedItems()
        if not sel:
            QMessageBox.warning(self, "Ошибка", "Выберите тип из списка.")
            return
        qualified_type = sel[0].text()
        dlg = ApplyTypeDialog(self.db_manager, qualified_type, parent=self)
        if dlg.exec() != QDialog.Accepted:
            return
        res = dlg.get_result()
        if not res:
            return
        table = res['table']
        column = res['column']
        is_new = res.get('is_new', False)

        if not is_new:
            reply = QMessageBox.question(self, "Подтвердите изменение типа",
                                         f"При изменении типа столбца {table}.{column} все данные в нём будут удалены.\n"
                                         "Продолжить?",
                                         QMessageBox.Yes | QMessageBox.No)
            if reply != QMessageBox.Yes:
                return


        try:
            try:
                sql = ("SELECT tc.constraint_name, tc.constraint_type "
                       "FROM information_schema.table_constraints tc "
                       "JOIN information_schema.key_column_usage kcu "
                       "  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema "
                       "WHERE tc.table_schema = %s AND tc.table_name = %s AND kcu.column_name = %s")
                tbl_schema = 'public'
                tbl_name = table
                if '.' in table:
                    tbl_schema, tbl_name = table.split('.', 1)
                cur = self.db_manager.execute(sql, (tbl_schema, tbl_name, column))
                constraints = []
                if cur:
                    try:
                        rows = cur.fetchall()
                        for r in rows:
                            constraints.append(r[0])
                    finally:
                        try:
                            cur.close()
                        except Exception:
                            pass
                for cons in constraints:
                    try:
                        sql_drop = f"ALTER TABLE {_quote_ident(table)} DROP CONSTRAINT {_quote_ident(cons)}"
                        self.db_manager.execute(sql_drop)
                    except Exception:
                        # если падает — логируем и продолжаем
                        logging.exception("drop constraint failed for %s.%s -> %s", table, column, cons)
                        pass
            except Exception:
                pass

            try:
                self.db_manager.execute(f"ALTER TABLE {_quote_ident(table)} ALTER COLUMN {_quote_ident(column)} DROP DEFAULT")
            except Exception:
                logging.exception("drop default failed")

            try:
                self.db_manager.execute(f"ALTER TABLE {_quote_ident(table)} ALTER COLUMN {_quote_ident(column)} DROP NOT NULL")
            except Exception:
                logging.exception("drop not null failed")

            try:
                if hasattr(self.db_manager, "connection") and getattr(self.db_manager, "connection", None) is not None:
                    try:
                        self.db_manager.connection.commit()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            logging.exception("constraint removal failed (continuing)")

        try:
            upd_sql = f"UPDATE {_quote_ident(table)} SET {_quote_ident(column)} = NULL"
            self.db_manager.execute(upd_sql)
            try:
                if hasattr(self.db_manager, "connection") and getattr(self.db_manager, "connection", None) is not None:
                    try:
                        self.db_manager.connection.commit()
                    except Exception:
                        pass
            except Exception:
                pass
        except Exception:
            logging.exception("clear column data failed")

        try:
            schema_part, type_part = self._split_schema_name(qualified_type)
            q_schema = self._quote_ident_local(schema_part)
            q_type = self._quote_ident_local(type_part)
            type_ref = f"{q_schema}.{q_type}"

            is_enum = (self.kind_cb.currentText() == "Enum")
            is_composite = (self.kind_cb.currentText() == "Composite")

            if is_enum:
                using_expr = f"NULL::{type_ref}"
            elif is_composite:

                try:
                    descr = self._describe_composite(qualified_type)
                    n_fields = sum(1 for ln in descr.splitlines() if ln.strip().startswith("- "))
                    if n_fields <= 0:
                        n_fields = 1
                except Exception:
                    n_fields = 1
                nulls = ", ".join(["NULL"] * n_fields)
                using_expr = f"ROW({nulls})::{type_ref}"
            else:
                using_expr = f"NULL::{type_ref}"

            alter_sql = f"ALTER TABLE {_quote_ident(table)} ALTER COLUMN {_quote_ident(column)} TYPE {type_ref} USING {using_expr}"
            self.db_manager.execute(alter_sql)
            try:
                if hasattr(self.db_manager, "connection") and getattr(self.db_manager, "connection", None) is not None:
                    try:
                        self.db_manager.connection.commit()
                    except Exception:
                        pass
            except Exception:
                pass

            QMessageBox.information(self, "Успех", f"Тип столбца {table}.{column} успешно изменён на {qualified_type}")
            self.load_types()
        except Exception as e:
            logging.exception("apply type failed")
            QMessageBox.warning(self, "Ошибка", f"Не удалось применить тип:\n{e}")