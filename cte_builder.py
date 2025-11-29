# cte_builder.py
import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QLineEdit, QMessageBox,
    QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

from select import AdvancedSelectDialog


class CteBuilderDialog(QDialog):
    def __init__(self, dbmanager, parent=None):
        super().__init__(parent)
        self.dbmanager = dbmanager
        self.setWindowTitle("WITH / CTE конструктор")
        self.resize(1000, 700)
        self.ctes = []  
        self.main_sql = ""
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("CTE (WITH):"))
        top_row.addStretch()
        layout.addLayout(top_row)

        self.cte_list = QListWidget()
        layout.addWidget(self.cte_list)

        btn_cte_row = QHBoxLayout()
        self.btn_add_cte = QPushButton("Добавить / изменить CTE")
        self.btn_delete_cte = QPushButton("Удалить CTE")
        self.btn_clear_cte = QPushButton("Очистить все CTE")

        self.btn_add_cte.clicked.connect(self.add_or_edit_cte)
        self.btn_delete_cte.clicked.connect(self.delete_cte)
        self.btn_clear_cte.clicked.connect(self.clear_ctes)

        btn_cte_row.addWidget(self.btn_add_cte)
        btn_cte_row.addWidget(self.btn_delete_cte)
        btn_cte_row.addWidget(self.btn_clear_cte)
        btn_cte_row.addStretch()
        layout.addLayout(btn_cte_row)

        name_row = QHBoxLayout()
        name_row.addWidget(QLabel("Имя CTE:"))
        self.cte_name_edit = QLineEdit()
        name_row.addWidget(self.cte_name_edit)
        layout.addLayout(name_row)

        main_row = QHBoxLayout()
        main_row.addWidget(QLabel("Основной SELECT:"))
        self.btn_build_main = QPushButton("Собрать SELECT")
        self.btn_build_main.clicked.connect(self.build_main_sql)
        main_row.addWidget(self.btn_build_main)
        main_row.addStretch()
        layout.addLayout(main_row)

        self.sql_preview = QTextEdit()
        self.sql_preview.setReadOnly(True)
        layout.addWidget(self.sql_preview)

        btn_exec_row = QHBoxLayout()
        self.btn_refresh_preview = QPushButton("Обновить текст SQL")
        self.btn_execute = QPushButton("Выполнить запрос")
        self.btn_close = QPushButton("Закрыть")

        self.btn_refresh_preview.clicked.connect(self.update_preview)
        self.btn_execute.clicked.connect(self.execute_query)
        self.btn_close.clicked.connect(self.reject)

        btn_exec_row.addWidget(self.btn_refresh_preview)
        btn_exec_row.addWidget(self.btn_execute)
        btn_exec_row.addStretch()
        btn_exec_row.addWidget(self.btn_close)
        layout.addLayout(btn_exec_row)

        layout.addWidget(QLabel("Результат:"))

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(0)
        self.result_table.setRowCount(0)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.result_table)

    def _get_builder_sql(self):
        dlg = AdvancedSelectDialog(self.dbmanager, self)
        if dlg.exec() != QDialog.Accepted:
            return None
        sql = dlg.sqlpreview.toPlainText().strip()
        if not sql.upper().startswith("SELECT"):
            QMessageBox.warning(self, "Ошибка", "Конструктор должен сформировать SELECT-запрос.")
            return None
        return sql

    def add_or_edit_cte(self):
        name = self.cte_name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Внимание", "Введите имя CTE.")
            return
        sql = self._get_builder_sql()
        if not sql:
            return

        existing = next((c for c in self.ctes if c["name"] == name), None)
        if existing:
            existing["sql"] = sql
        else:
            self.ctes.append({"name": name, "sql": sql})
            self.cte_list.addItem(QListWidgetItem(name))

        self.update_preview()

    def delete_cte(self):
        row = self.cte_list.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Внимание", "Выберите CTE для удаления.")
            return
        self.ctes.pop(row)
        self.cte_list.takeItem(row)
        self.update_preview()

    def clear_ctes(self):
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Удалить все CTE?",
            QMessageBox.Yes,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.ctes.clear()
        self.cte_list.clear()
        self.update_preview()

    def build_main_sql(self):
        sql = self._get_builder_sql()
        if not sql:
            return
        self.main_sql = sql
        self.update_preview()

    def build_full_sql(self):
        if not self.main_sql:
            return ""
        if not self.ctes:
            return self.main_sql
        parts = []
        parts.append("WITH")
        cte_parts = []
        for c in self.ctes:
            cte_parts.append(f"{c['name']} AS (\n{c['sql']}\n)")
        parts.append(",\n".join(cte_parts))
        parts.append(self.main_sql)
        return "\n".join(parts)

    def update_preview(self):
        full_sql = self.build_full_sql()
        self.sql_preview.setPlainText(full_sql)

    def execute_query(self):
        full_sql = self.build_full_sql()
        if not full_sql:
            QMessageBox.warning(self, "Ошибка", "Нужно задать основной SELECT.")
            return
        try:
            cur = self.dbmanager.executesql(full_sql)
            if not cur:
                return
            rows = cur.fetchall()
            desc = cur.description
            cur.close()

            columns = [d[0] for d in desc] if desc else []
            self.result_table.setRowCount(len(rows))
            self.result_table.setColumnCount(len(columns))
            self.result_table.setHorizontalHeaderLabels(columns)

            for i, row in enumerate(rows):
                for j, val in enumerate(row):
                    item = QTableWidgetItem("" if val is None else str(val))
                    self.result_table.setItem(i, j, item)
        except Exception as e:
            logging.exception("CTE execute failed: %s", e)
            QMessageBox.warning(self, "Ошибка", str(e))
