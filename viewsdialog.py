import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QTableWidget,
    QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt

from select import AdvancedSelectDialog


class ViewsDialog(QDialog):
    def __init__(self, dbmanager, parent=None):
        super().__init__(parent)
        self.dbmanager = dbmanager
        self.setWindowTitle("Представления (VIEW / MATERIALIZED VIEW)")
        self.resize(900, 600)
        self.setup_ui()
        self.load_views()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        top_row = QHBoxLayout()
        top_row.addWidget(QLabel("Существующие представления:"))
        top_row.addStretch()
        layout.addLayout(top_row)

        self.views_list = QListWidget()
        layout.addWidget(self.views_list)

        btn_row = QHBoxLayout()
        self.btn_create_view = QPushButton("Создать VIEW")
        self.btn_create_mat_view = QPushButton("Создать MATERIALIZED VIEW")
        self.btn_refresh_mat_view = QPushButton("REFRESH MATERIALIZED VIEW")
        self.btn_drop = QPushButton("Удалить")
        self.btn_preview = QPushButton("Просмотреть данные")

        self.btn_create_view.clicked.connect(self.create_view)
        self.btn_create_mat_view.clicked.connect(self.create_materialized_view)
        self.btn_refresh_mat_view.clicked.connect(self.refresh_materialized_view)
        self.btn_drop.clicked.connect(self.drop_view)
        self.btn_preview.clicked.connect(self.preview_view)

        btn_row.addWidget(self.btn_create_view)
        btn_row.addWidget(self.btn_create_mat_view)
        btn_row.addWidget(self.btn_refresh_mat_view)
        btn_row.addWidget(self.btn_preview)
        btn_row.addWidget(self.btn_drop)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        layout.addWidget(QLabel("Результат выборки:"))

        self.result_table = QTableWidget()
        self.result_table.setColumnCount(0)
        self.result_table.setRowCount(0)
        self.result_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.result_table)

    def load_views(self):
        self.views_list.clear()
        items = []
        
        try:
           
            sql_views = (
                "SELECT table_schema, table_name, 'VIEW' as view_type "
                "FROM information_schema.views "
                "WHERE table_schema NOT IN ('pg_catalog','information_schema') "
            )
            
      
            sql_matviews = (
                "SELECT schemaname, matviewname, 'MATERIALIZED VIEW' as view_type "
                "FROM pg_matviews "
                "WHERE schemaname NOT IN ('pg_catalog','information_schema') "
            )
            
      
            sql = f"{sql_views} UNION ALL {sql_matviews} ORDER BY 1, 2"
            
            cur = self.dbmanager.execute(sql)
            if not cur:
                return
            rows = cur.fetchall()
            cur.close()
            
            items = [f"{r[0]}.{r[1]} ({r[2]})" for r in rows]
            
        except Exception as e:
            logging.exception("load_views failed: %s", e)
            QMessageBox.critical(
                self,
                "Ошибка",
                f"Не удалось получить список представлений:\n{str(e)}",
            )
            items = []
        
        for name in items:
            self.views_list.addItem(QListWidgetItem(name))



    def _get_selected_view(self):
        items = self.views_list.selectedItems()
        if not items:
            QMessageBox.warning(self, "Внимание", "Выберите представление в списке.")
            return None
        
        full_text = items[0].text()
        import re
        name = re.sub(r'\s*\(.*?\)\s*$', '', full_text).strip()
        
        return name


    def _make_select_with_builder(self):
        dlg = AdvancedSelectDialog(self.dbmanager, self)
        
       
        result_sql = None
        
        def on_apply(sql):
            nonlocal result_sql
            result_sql = sql
        
        dlg.apply_sql.connect(on_apply)
        dlg.exec()  
        
    
        if result_sql:
            sql = result_sql
        else:
           
            sql = dlg.sqlpreview.toPlainText().strip()
        
        if not sql or not sql.upper().startswith("SELECT"):
            return None
        
        return sql

    def create_view(self):
        base_sql = self._make_select_with_builder()
        if not base_sql:
            return
        name, ok = self._ask_view_name()
        if not ok or not name:
            return
        try:
            full_sql = f"CREATE OR REPLACE VIEW {name} AS\n{base_sql}"
            self.dbmanager.execute(full_sql)
            if getattr(self.dbmanager, "connection", None):
                try:
                    self.dbmanager.connection.commit()
                except Exception:
                    pass
            QMessageBox.information(self, "Готово", f"VIEW {name} создано/обновлено.")
            self.load_views()
        except Exception as e:
            logging.exception("create_view failed: %s", e)
            QMessageBox.warning(self, "Ошибка", str(e))

    def create_materialized_view(self):
        base_sql = self._make_select_with_builder()
        if not base_sql:
            return
        name, ok = self._ask_view_name()
        if not ok or not name:
            return
        try:
            full_sql = f"CREATE MATERIALIZED VIEW {name} AS\n{base_sql}"
            self.dbmanager.execute(full_sql)
            if getattr(self.dbmanager, "connection", None):
                try:
                    self.dbmanager.connection.commit()
                except Exception:
                    pass
            QMessageBox.information(self, "Готово", f"MATERIALIZED VIEW {name} создано.")
            self.load_views()
        except Exception as e:
            logging.exception("create_materialized_view failed: %s", e)
            QMessageBox.warning(self, "Ошибка", str(e))

    def refresh_materialized_view(self):
        name = self._get_selected_view()
        if not name:
            return
        try:
            sql = f"REFRESH MATERIALIZED VIEW {name}"
            self.dbmanager.execute(sql)
            if getattr(self.dbmanager, "connection", None):
                try:
                    self.dbmanager.connection.commit()
                except Exception:
                    pass
            QMessageBox.information(self, "Готово", f"{name} обновлено.")
        except Exception as e:
            logging.exception("refresh_materialized_view failed: %s", e)
            QMessageBox.warning(self, "Ошибка", str(e))

    def drop_view(self):
        name = self._get_selected_view()
        if not name:
            return
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            f"Удалить {name}?",
            QMessageBox.Yes,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            sql = f"DROP VIEW IF EXISTS {name} CASCADE"
            self.dbmanager.execute(sql)
            if getattr(self.dbmanager, "connection", None):
                try:
                    self.dbmanager.connection.commit()
                except Exception:
                    pass
            QMessageBox.information(self, "Готово", f"{name} удалено.")
            self.load_views()
        except Exception as e:
            logging.exception("drop_view failed: %s", e)
            QMessageBox.warning(self, "Ошибка", str(e))

    def preview_view(self):
        name = self._get_selected_view()
        if not name:
            return
        try:
            sql = f"SELECT * FROM {name} LIMIT 200"
            cur = self.dbmanager.execute(sql)
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
            logging.exception("preview_view failed: %s", e)
            QMessageBox.warning(self, "Ошибка", str(e))

    def _ask_view_name(self):
        from PySide6.QtWidgets import QInputDialog
        name, ok = QInputDialog.getText(
            self,
            "Имя представления",
            "Введите имя (schema.view_name или view_name):",
        )
        name = name.strip()
        return name, ok
