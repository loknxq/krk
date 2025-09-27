import psycopg2
import logging
import os
from datetime import datetime
from typing import List, Tuple, Optional, Dict

class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connection_params = {
            'dbname': 'postgres',
            'user': 'postgres',
            'password': "",
            'host': 'localhost',
            'port': '5432'
        }
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(
            filename='app.log',
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            encoding='utf-8'
        )

    def set_connection_params(self, params: Dict):
        self.connection_params.update(params)

    def get_connection_params(self):
        return self.connection_params.copy()

    def connect(self) -> bool:
        try:
            self.connection = psycopg2.connect(**self.connection_params)
            logging.info("Успешное подключение к БД")
            return True
        except Exception as e:
            logging.error(f"Ошибка подключения к БД: {str(e)}")
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()
            self.connection = None
            logging.info("Отключение от БД")

    def is_connected(self) -> bool:
        if self.connection:
            try:
                cursor = self.connection.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return True
            except Exception as e:
                logging.error(f"Ошибка проверки подключения: {str(e)}")
                self.connection = None
                return False
        return False


    def recreate_tables(self) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False

            cursor = self.connection.cursor()

            # Удаляем существующие таблицы
            tables = ['transactions', 'products', 'employees', 'points']
            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

            # Создаем таблицы заново
            scripts = [
                """
                CREATE TABLE points (
                    point_id SERIAL PRIMARY KEY,
                    address VARCHAR(200) NOT NULL,
                    phone_number VARCHAR(20),
                    manager_id INTEGER NULL
                )
                """,
                """
                CREATE TABLE employees (
                    employee_id SERIAL PRIMARY KEY,
                    full_name VARCHAR(150) NOT NULL,
                    position VARCHAR(100) NOT NULL,
                    salary DECIMAL(10, 2) NOT NULL CHECK (salary >= 0),
                    schedule VARCHAR(50) NOT NULL,
                    point_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (point_id) REFERENCES points(point_id) ON DELETE CASCADE
                )
                """,
                """
                ALTER TABLE points
                ADD CONSTRAINT fk_points_manager
                FOREIGN KEY (manager_id) REFERENCES employees(employee_id)
                """,
                """
                CREATE TABLE products (
                    product_id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    category VARCHAR(50) NOT NULL,
                    cost_price DECIMAL(10, 2) NOT NULL CHECK (cost_price >= 0),
                    selling_price DECIMAL(10, 2) NOT NULL CHECK (selling_price >= 0),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE transactions (
                    transaction_id SERIAL PRIMARY KEY,
                    point_id INTEGER NOT NULL,
                    type VARCHAR(20) NOT NULL CHECK (type IN ('Доход', 'Расход')),
                    amount DECIMAL(12, 2) NOT NULL CHECK (amount >= 0),
                    date DATE NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (point_id) REFERENCES points(point_id) ON DELETE CASCADE
                )
                """
            ]

            for script in scripts:
                cursor.execute(script)

            self.connection.commit()
            cursor.close()
            logging.info("Таблицы успешно пересозданы")
            return True

        except Exception as e:
            logging.error(f"Ошибка пересоздания таблиц: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def insert_sample_data(self) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False

            cursor = self.connection.cursor()

            sample_data = [
                # Точки
                "INSERT INTO points (address, phone_number) VALUES ('ул. Главная, 1', '+7 (495) 111-22-33')",
                "INSERT INTO points (address, phone_number) VALUES ('пр. Мира, 45', '+7 (495) 222-33-44')",
                "INSERT INTO points (address, phone_number) VALUES ('ул. Рабочая, 12', '+7 (495) 333-44-55')",

                # Сотрудники
                "INSERT INTO employees (full_name, position, salary, schedule, point_id) VALUES ('Иванов Иван Иванович', 'администратор', 50000.00, '5/2', 1)",
                "INSERT INTO employees (full_name, position, salary, schedule, point_id) VALUES ('Петрова Мария Сергеевна', 'кассир', 35000.00, '2/2', 1)",
                "INSERT INTO employees (full_name, position, salary, schedule, point_id) VALUES ('Сидоров Алексей Петрович', 'повар', 45000.00, '2/2', 1)",
                "INSERT INTO employees (full_name, position, salary, schedule, point_id) VALUES ('Кузнецова Елена Викторовна', 'кассир', 32000.00, '5/2', 2)",
                "INSERT INTO employees (full_name, position, salary, schedule, point_id) VALUES ('Васильев Дмитрий Олегович', 'повар', 42000.00, '2/2', 2)",
                "INSERT INTO employees (full_name, position, salary, schedule, point_id) VALUES ('Николаева Ольга Игоревна', 'администратор', 48000.00, '5/2', 3)",
                "INSERT INTO employees (full_name, position, salary, schedule, point_id) VALUES ('Смирнов Артем Александрович', 'повар', 43000.00, '2/2', 3)",
                "INSERT INTO employees (full_name, position, salary, schedule, point_id) VALUES ('Федорова Анна Дмитриевна', 'кассир', 33000.00, '5/2', 3)",

                # Назначение менеджеров
                "UPDATE points SET manager_id = 1 WHERE point_id = 1",
                "UPDATE points SET manager_id = 6 WHERE point_id = 3",

                # Продукты
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Крошка Картошка с растительным маслом', 'основной картофель', 35.00, 189.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Крошка Картошка с сыром', 'основной картофель', 45.00, 219.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Крошка Картошка со сливочным маслом', 'основной картофель', 38.00, 199.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Крошка Картошка с укропом и растительным маслом', 'основной картофель', 40.00, 209.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Печёный МЭШ Классический', 'основной картофель', 30.00, 159.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Печёный Мэш Классический (большой)', 'основной картофель', 50.00, 229.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Наполнитель \"Брынзовый с укропом\"', 'наполнители', 25.00, 89.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Наполнитель \"Крабовое мясо с майонезом\"', 'наполнители', 28.00, 99.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Наполнитель \"Сосиски в горчичном соусе\"', 'наполнители', 30.00, 109.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Наполнитель \"Сырный с ветчиной\"', 'наполнители', 32.00, 119.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Наполнитель \"Закусочный с грибами\"', 'наполнители', 29.00, 104.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Наполнитель \"Мясное ассорти\"', 'наполнители', 35.00, 129.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Наполнитель \"Красная рыбка\"', 'наполнители', 40.00, 149.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Наполнитель \"Цыпленок с жареными грибами\"', 'наполнители', 33.00, 124.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Борщ', 'супы', 45.00, 159.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Куриная лапша', 'супы', 40.00, 149.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Гороховый суп', 'супы', 42.00, 154.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Сливочная уха по-фински', 'супы', 50.00, 179.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Пирожное Картошка', 'десерты', 20.00, 89.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Пирожное картошка \"Орех в карамели\"', 'десерты', 25.00, 109.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Пирожное картошка Кокос', 'десерты', 23.00, 99.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Пирожное \"Чиакейк маракуйя-облепиха\"', 'десерты', 35.00, 149.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Морс Ягодный 0.5л', 'напитки', 15.00, 129.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Напиток «Добрый Pulpy» 0.45л', 'напитки', 18.00, 139.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Сок Добрый 0.3л', 'напитки', 12.00, 99.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Квас 0.4л', 'напитки', 10.00, 89.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Чай черный', 'напитки', 5.00, 79.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Чай зеленый', 'напитки', 5.00, 79.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Кофе американо', 'напитки', 8.00, 119.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Сметана', 'добавки', 8.00, 49.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Кетчуп', 'соусы', 6.00, 39.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Майонез', 'соусы', 6.00, 39.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Горчица', 'соусы', 5.00, 29.00)",
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES ('Сырный соус', 'соусы', 10.00, 59.00)",

                # Финансовые операции
                # Точка 1
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (1, 'Доход', 42350.00, '2024-01-15', 'Выручка за понедельник')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (1, 'Доход', 48700.00, '2024-01-16', 'Выручка за вторник')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (1, 'Доход', 53200.00, '2024-01-17', 'Выручка за среду')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (1, 'Доход', 59800.00, '2024-01-18', 'Выручка за четверг')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (1, 'Доход', 72300.00, '2024-01-19', 'Выручка за пятницу')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (1, 'Доход', 84500.00, '2024-01-20', 'Выручка за субботу')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (1, 'Доход', 71200.00, '2024-01-21', 'Выручка за воскресенье')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (1, 'Расход', 45000.00, '2024-01-15', 'Зарплата сотрудникам')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (1, 'Расход', 28500.00, '2024-01-15', 'Закупка продуктов')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (1, 'Расход', 15000.00, '2024-01-15', 'Аренда и коммунальные услуги')",

                # Точка 2
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (2, 'Доход', 31200.00, '2024-01-15', 'Выручка за понедельник')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (2, 'Доход', 35600.00, '2024-01-16', 'Выручка за вторник')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (2, 'Доход', 39800.00, '2024-01-17', 'Выручка за среду')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (2, 'Доход', 44500.00, '2024-01-18', 'Выручка за четверг')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (2, 'Доход', 52300.00, '2024-01-19', 'Выручка за пятницу')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (2, 'Доход', 61200.00, '2024-01-20', 'Выручка за субботу')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (2, 'Доход', 48700.00, '2024-01-21', 'Выручка за воскресенье')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (2, 'Расход', 32000.00, '2024-01-15', 'Зарплата сотрудникам')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (2, 'Расход', 19800.00, '2024-01-15', 'Закупка продуктов')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (2, 'Расход', 12000.00, '2024-01-15', 'Аренда и коммунальные услуги')",

                # Точка 3
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (3, 'Доход', 25800.00, '2024-01-15', 'Выручка за понедельник')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (3, 'Доход', 29400.00, '2024-01-16', 'Выручка за вторник')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (3, 'Доход', 33200.00, '2024-01-17', 'Выручка за среду')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (3, 'Доход', 37800.00, '2024-01-18', 'Выручка за четверг')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (3, 'Доход', 44500.00, '2024-01-19', 'Выручка за пятницу')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (3, 'Доход', 52300.00, '2024-01-20', 'Выручка за субботу')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (3, 'Доход', 41200.00, '2024-01-21', 'Выручка за воскресенье')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (3, 'Расход', 38000.00, '2024-01-15', 'Зарплата сотрудникам')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (3, 'Расход', 22400.00, '2024-01-15', 'Закупка продуктов')",
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (3, 'Расход', 18000.00, '2024-01-15', 'Аренда и коммунальные услуги')"
            ]

            for query in sample_data:
                cursor.execute(query)

            cursor.execute("UPDATE points SET manager_id = 1 WHERE point_id = 1")
            cursor.execute("UPDATE points SET manager_id = 4 WHERE point_id = 2")

            self.connection.commit()
            cursor.close()
            logging.info("Тестовые данные добавлены")
            return True

        except Exception as e:
            logging.error(f"Ошибка добавления тестовых данных: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def get_points(self) -> List[Tuple]:
        try:
            if not self.is_connected():
                if not self.connect():
                    return []
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM points ORDER BY point_id")
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения точек: {str(e)}")
            return []

    def get_employees(self) -> List[Tuple]:
        try:
            if not self.is_connected():
                if not self.connect():
                    return []
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM employees ORDER BY employee_id")
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения сотрудников: {str(e)}")
            return []

    def get_products(self) -> List[Tuple]:
        try:
            if not self.is_connected():
                if not self.connect():
                    return []
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM products ORDER BY product_id")
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения продуктов: {str(e)}")
            return []

    def get_finances(self) -> List[Tuple]:
        try:
            if not self.is_connected():
                if not self.connect():
                    return []
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM transactions ORDER BY transaction_id")
            result = cursor.fetchall()
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения финансов: {str(e)}")
            return []

    # МЕТОДЫ ДЛЯ ДОБАВЛЕНИЯ ДАННЫХ
    def insert_point(self, address: str, phone_number: str = None) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO points (address, phone_number) VALUES (%s, %s)",
                (address, phone_number)
            )
            self.connection.commit()
            cursor.close()
            logging.info(f"Добавлена точка: {address}")
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления точки: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def insert_employee(self, full_name: str, position: str, salary: float, schedule: str, point_id: int) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO employees (full_name, position, salary, schedule, point_id) VALUES (%s, %s, %s, %s, %s)",
                (full_name, position, salary, schedule, point_id)
            )
            self.connection.commit()
            cursor.close()
            logging.info(f"Добавлен сотрудник: {full_name}")
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления сотрудника: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def insert_product(self, name: str, category: str, cost_price: float, selling_price: float) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO products (name, category, cost_price, selling_price) VALUES (%s, %s, %s, %s)",
                (name, category, cost_price, selling_price)
            )
            self.connection.commit()
            cursor.close()
            logging.info(f"Добавлен продукт: {name}")
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления продукта: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def insert_transaction(self, point_id: int, type: str, amount: float, date: str, description: str = None) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute(
                "INSERT INTO transactions (point_id, type, amount, date, description) VALUES (%s, %s, %s, %s, %s)",
                (point_id, type, amount, date, description)
            )
            self.connection.commit()
            cursor.close()
            logging.info(f"Добавлена операция: {type} на сумму {amount}")
            return True
        except Exception as e:
            logging.error(f"Ошибка добавления операции: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def delete_point(self, point_id: int) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM points WHERE point_id = %s", (point_id,))
            self.connection.commit()
            cursor.close()
            logging.info(f"Удалена точка ID: {point_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления точки: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def delete_employee(self, employee_id: int) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM employees WHERE employee_id = %s", (employee_id,))
            self.connection.commit()
            cursor.close()
            logging.info(f"Удален сотрудник ID: {employee_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления сотрудника: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def delete_product(self, product_id: int) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM products WHERE product_id = %s", (product_id,))
            self.connection.commit()
            cursor.close()
            logging.info(f"Удален продукт ID: {product_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления продукта: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False
    def delete_transaction(self, transaction_id: int) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute("DELETE FROM transactions WHERE transaction_id = %s", (transaction_id,))
            self.connection.commit()
            cursor.close()
            logging.info(f"Удалена финансовая операция ID: {transaction_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка удаления финансовой операции: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    # МЕТОДЫ ДЛЯ ПОЛУЧЕНИЯ СТАТИСТИКИ
    def get_points_count(self) -> int:
        try:
            if not self.is_connected():
                if not self.connect():
                    return 0
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM points")
            result = cursor.fetchone()[0]
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения количества точек: {str(e)}")
            return 0

    def get_employees_count(self) -> int:
        try:
            if not self.is_connected():
                if not self.connect():
                    return 0
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM employees")
            result = cursor.fetchone()[0]
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения количества сотрудников: {str(e)}")
            return 0

    def get_products_count(self) -> int:
        try:
            if not self.is_connected():
                if not self.connect():
                    return 0
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            result = cursor.fetchone()[0]
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения количества продуктов: {str(e)}")
            return 0

    def get_total_revenue(self) -> float:
        try:
            if not self.is_connected():
                if not self.connect():
                    return 0.0
            cursor = self.connection.cursor()
            cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Доход'")
            result = cursor.fetchone()[0] or 0.0
            cursor.close()
            return float(result)
        except Exception as e:
            logging.error(f"Ошибка получения общего дохода: {str(e)}")
            return 0.0

    def get_total_expenses(self) -> float:
        try:
            if not self.is_connected():
                if not self.connect():
                    return 0.0
            cursor = self.connection.cursor()
            cursor.execute("SELECT SUM(amount) FROM transactions WHERE type = 'Расход'")
            result = cursor.fetchone()[0] or 0.0
            cursor.close()
            return float(result)
        except Exception as e:
            logging.error(f"Ошибка получения общих расходов: {str(e)}")
            return 0.0

    # МЕТОД ДЛЯ ПОЛУЧЕНИЯ ЛОГОВ
    def get_logs(self) -> List[str]:
        try:
            with open('app.log', 'r', encoding='utf-8') as f:
                return f.readlines()
        except Exception as e:
            logging.error(f"Ошибка чтения логов: {str(e)}")
            return ["Логи не найдены"]

    def check_data_exists(self) -> Dict[str, bool]:
        result = {
            'points': False,
            'employees': False,
            'products': False,
            'transactions': False
        }
        
        try:
            if not self.is_connected():
                if not self.connect():
                    return result
            
            cursor = self.connection.cursor()
            
            cursor.execute("SELECT EXISTS(SELECT 1 FROM points LIMIT 1)")
            result['points'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT EXISTS(SELECT 1 FROM employees LIMIT 1)")
            result['employees'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT EXISTS(SELECT 1 FROM products LIMIT 1)")
            result['products'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT EXISTS(SELECT 1 FROM transactions LIMIT 1)")
            result['transactions'] = cursor.fetchone()[0]
            
            cursor.close()
            
        except Exception as e:
            logging.error(f"Ошибка проверки данных: {str(e)}")
        
        return result

    def update_point(self, point_id: int, address: str, phone_number: str = None) -> bool:
        """Обновляет данные точки"""
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE points SET address = %s, phone_number = %s WHERE point_id = %s",
                (address, phone_number, point_id)
            )
            self.connection.commit()
            cursor.close()
            logging.info(f"Обновлена точка ID: {point_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка обновления точки: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def update_employee(self, employee_id: int, full_name: str, position: str, salary: float, schedule: str, point_id: int) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE employees SET full_name = %s, position = %s, salary = %s, schedule = %s, point_id = %s WHERE employee_id = %s",
                (full_name, position, salary, schedule, point_id, employee_id)
            )
            self.connection.commit()
            cursor.close()
            logging.info(f"Обновлен сотрудник ID: {employee_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка обновления сотрудника: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def update_product(self, product_id: int, name: str, category: str, cost_price: float, selling_price: float) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE products SET name = %s, category = %s, cost_price = %s, selling_price = %s WHERE product_id = %s",
                (name, category, cost_price, selling_price, product_id)
            )
            self.connection.commit()
            cursor.close()
            logging.info(f"Обновлен продукт ID: {product_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка обновления продукта: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def update_transaction(self, transaction_id: int, point_id: int, type: str, amount: float, date: str, description: str = None) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            
            cursor = self.connection.cursor()
            cursor.execute(
                "UPDATE transactions SET point_id = %s, type = %s, amount = %s, date = %s, description = %s WHERE transaction_id = %s",
                (point_id, type, amount, date, description, transaction_id)
            )
            self.connection.commit()
            cursor.close()
            logging.info(f"Обновлена финансовая операция ID: {transaction_id}")
            return True
        except Exception as e:
            logging.error(f"Ошибка обновления финансовой операции: {str(e)}")
            if self.connection:
                self.connection.rollback()
            return False

    def get_point_by_id(self, point_id: int) -> Tuple:
        try:
            if not self.is_connected():
                if not self.connect():
                    return None
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM points WHERE point_id = %s", (point_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения точки: {str(e)}")
            return None

    def get_employee_by_id(self, employee_id: int) -> Tuple:
        try:
            if not self.is_connected():
                if not self.connect():
                    return None
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM employees WHERE employee_id = %s", (employee_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения сотрудника: {str(e)}")
            return None

    def get_product_by_id(self, product_id: int) -> Tuple:
        try:
            if not self.is_connected():
                if not self.connect():
                    return None
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM products WHERE product_id = %s", (product_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения продукта: {str(e)}")
            return None

    def get_transaction_by_id(self, transaction_id: int) -> Tuple:
        try:
            if not self.is_connected():
                if not self.connect():
                    return None
            cursor = self.connection.cursor()
            cursor.execute("SELECT * FROM transactions WHERE transaction_id = %s", (transaction_id,))
            result = cursor.fetchone()
            cursor.close()
            return result
        except Exception as e:
            logging.error(f"Ошибка получения финансовой операции: {str(e)}")
            return None