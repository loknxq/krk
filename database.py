from types import SimpleNamespace

import psycopg2
import logging
import os
import re
from datetime import datetime
from typing import List, Tuple, Optional, Dict
from string import ascii_letters
import logging
from typing import Dict, Any, List, Optional, Tuple
class DatabaseManager:
    def __init__(self):
        self.connection = None
        self.connection_params = {
            'dbname': 'subo',
            'user': 'postgres',
            'password': "postgres",
            'host': 'localhost',
            'port': '5432'
        }
        self.structure_changed = False
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

            tables = self.list_tables()

            for table in tables:
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")

            cursor.execute("DROP TYPE IF EXISTS transaction_type CASCADE")
            cursor.execute("CREATE TYPE transaction_type AS ENUM ('Доход', 'Расход')")

            scripts = [
                """
                CREATE TABLE points (
                    point_id SERIAL PRIMARY KEY,
                    address VARCHAR(200) NOT NULL CHECK (length(address) >= 5 AND address ~ '^[А-Яа-я0-9\\s\\.,-]+$'),
                    phone_number CHAR(11) CHECK (
                        phone_number IS NULL OR 
                        (
                            length(phone_number) = 11 AND
                            phone_number ~ '^8\\d{10}$'
                        )
                    ),
                    manager_id INTEGER NULL
                )
                """,
                """
                CREATE TABLE employees (
                    employee_id SERIAL PRIMARY KEY,
                    full_name VARCHAR(150) NOT NULL CHECK (
                        length(full_name) >= 5 AND 
                        full_name ~ '^[A-Za-zА-Яа-я\\s\\-]+$' AND
                        full_name ~ '\\s'  -- должен содержать пробел (имя и фамилия)
                    ),
                    position VARCHAR(100) NOT NULL CHECK (length(position) >= 2),
                    salary DECIMAL(10, 2) NOT NULL CHECK (salary >= 0),
                    schedule VARCHAR(50) NOT NULL CHECK (length(schedule) >= 2),
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
                    name VARCHAR(100) NOT NULL CHECK (length(name) >= 2),
                    category VARCHAR(50) NOT NULL CHECK (length(category) >= 2),
                    cost_price DECIMAL(10, 2) NOT NULL CHECK (cost_price >= 0),
                    selling_price DECIMAL(10, 2) NOT NULL CHECK (selling_price >= 0 AND selling_price >= cost_price),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """,
                """
                CREATE TABLE transactions (
                    transaction_id SERIAL PRIMARY KEY,
                    point_id INTEGER NOT NULL,
                    type transaction_type NOT NULL,
                    amount DECIMAL(12, 2) NOT NULL CHECK (amount >= 0),
                    date DATE NOT NULL CHECK (date >= '2000-01-01' AND date <= CURRENT_DATE + INTERVAL '1 year'),
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

                "INSERT INTO points (address, phone_number) VALUES ('ул. Главная, 1', '84951112233')",
                "INSERT INTO points (address, phone_number) VALUES ('пр. Мира, 45', '84952223344')",
                "INSERT INTO points (address, phone_number) VALUES ('ул. Рабочая, 12', '84953334455')",

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

            # Назначаем менеджеров для точек
            cursor.execute("UPDATE points SET manager_id = 1 WHERE point_id = 1")
            cursor.execute("UPDATE points SET manager_id = 6 WHERE point_id = 3")

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

    def is_valid_phone(self, phone_number):
        pattern = r'^(\+7|7|8)?[\s\-]?\(?[489][0-9]{2}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$'
        return bool(re.match(pattern, phone_number))
    
    def is_valid_ru_letters(self, name):
        for i in name:
            if i in ascii_letters:
                return False
        return True
    
    def is_valid_schedule(self, schedule):
        pattern = r'[1-7]/[0-6]'
        return bool(re.match(pattern, schedule))

    def insert_point(self, address: str, phone_number: str = None) -> bool:
        try:
            if not self.is_valid_phone(phone_number) or not self.is_valid_ru_letters(address):
                logging.error("Неверный формат")
                return False
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
            if not self.is_valid_ru_letters(full_name) or not self.is_valid_schedule(schedule) or not self.is_valid_ru_letters(position):
                logging.error('Ошибка добавления сотрудника')
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
            if not self.is_valid_ru_letters(name) or not self.is_valid_ru_letters(category):
                logging.error("Ошибка добавления продукта")
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
            if not self.is_valid_ru_letters(description):
                logging.error(f'Неверный формат:{description}')
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
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
                
            if not self.is_valid_phone(phone_number) or not self.is_valid_ru_letters(address):
                logging.error("Неверный формат")
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
            if not self.is_valid_ru_letters(full_name) or not self.is_valid_schedule(schedule) or not self.is_valid_ru_letters(position):
                logging.error('Ошибка добавления сотрудника')
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
            if not self.is_valid_ru_letters(name) or not self.is_valid_ru_letters(category):
                logging.error("Ошибка добавления продукта")
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
            if not self.is_valid_ru_letters(description):
                logging.error(f'Неверный формат:{description}')
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

    def refresh_connection(self):
        try:
            if self.connection:
                self.connection.rollback()
                self.disconnect()
                return self.connect()
        except Exception as e:
            logging.error(f"Ошибка обновления соединения: {str(e)}")
            return False
        return True

    def mark_structure_changed(self):
        """Пометить что структура БД была изменена"""
        self.structure_changed = True

    def clear_structure_changed(self):
        """Сбросить флаг изменений"""
        self.structure_changed = False

    def has_structure_changed(self):
        """Проверить были ли изменения структуры"""
        return self.structure_changed

    def list_tables(self) -> List[str]:

        try:
            if not self.is_connected():
                if not self.connect():
                    return []
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                ORDER BY table_name
            """)
            rows = cursor.fetchall()
            cursor.close()
            return [r[0] for r in rows]
        except Exception as e:
            logging.error(f"Ошибка получения списка таблиц: {str(e)}")
            return []

    def get_columns(self, table_name: str) -> List[str]:

        try:
            if not self.is_connected():
                if not self.connect():
                    return []
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_name = %s
                ORDER BY ordinal_position
            """, (table_name,))
            rows = cursor.fetchall()
            cursor.close()
            return [r[0] for r in rows]
        except Exception as e:
            logging.error(f"Ошибка получения колонок для таблицы {table_name}: {str(e)}")
            return []

    def get_table(self, table_name: str) -> Optional[SimpleNamespace]:

        try:
            cols = self.get_columns(table_name)
            if not cols:
                return None
            columns = [SimpleNamespace(name=c) for c in cols]
            table_obj = SimpleNamespace(name=table_name, columns=columns)
            return table_obj
        except Exception as e:
            logging.error(f"Ошибка get_table({table_name}): {e}")
            return None

    def execute(self, sql: str, params: Optional[Tuple] = None):

        try:
            if not self.is_connected():
                if not self.connect():
                    return None
            cursor = self.connection.cursor()
            if params is not None:
                cursor.execute(sql, params)
            else:
                cursor.execute(sql)
            return cursor
        except Exception as e:
            logging.error(f"Ошибка выполнения запроса через DBManager.execute: {e}\nSQL: {sql}")
            try:
                cursor.close()
            except Exception:
                pass
            return None

    def get_column_metadata(self, table_name: str, column_name: str) -> Dict[str, Any]:

        try:
            if not self.is_connected():
                if not self.connect():
                    return {}
            cur = self.connection.cursor()
            cur.execute("""
                SELECT
                  column_name, data_type, is_nullable, column_default, udt_name
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = %s AND column_name = %s
                LIMIT 1
            """, (table_name, column_name))
            row = cur.fetchone()
            meta = {}
            if row:
                meta['table'] = table_name
                meta['column'] = row[0]
                meta['data_type'] = row[1]
                meta['is_nullable'] = (row[2] == 'YES')
                meta['column_default'] = row[3]
                meta['udt_name'] = row[4]  # внутреннее имя типа (важно для enum)
            else:
                try:
                    cur.close()
                except Exception:
                    pass
                return {}

            # primary key?
            cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = 'public' AND tc.table_name = %s AND tc.constraint_type = 'PRIMARY KEY'
                  AND kcu.column_name = %s
            """, (table_name, column_name))
            meta['is_primary'] = bool(cur.fetchone())

            cur.execute("""
                SELECT tc.constraint_name, array_agg(kcu.column_name ORDER BY kcu.ordinal_position)
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                WHERE tc.table_schema = 'public' AND tc.table_name = %s AND tc.constraint_type = 'UNIQUE'
                  AND kcu.column_name = %s
                GROUP BY tc.constraint_name
            """, (table_name, column_name))
            uniqs = []
            for cname, cols in cur.fetchall():
                uniqs.append({'name': cname, 'columns': cols})
            meta['unique_constraints'] = uniqs

            # check constraints that reference this column in expression (best-effort)
            cur.execute("""
                SELECT con.conname,
                       pg_get_constraintdef(con.oid) as consrc
                FROM pg_constraint con
                JOIN pg_class rel ON rel.oid = con.conrelid
                JOIN pg_namespace nsp ON nsp.oid = con.connamespace
                WHERE nsp.nspname = 'public' AND rel.relname = %s AND con.contype = 'c'
                  AND pg_get_constraintdef(con.oid) ILIKE %s
            """, (table_name, f'%{column_name}%'))
            checks = []
            for cname, expr in cur.fetchall():
                checks.append({'name': cname, 'expr': expr})
            meta['check_constraints'] = checks

            # foreign keys involving this column (best-effort)
            cur.execute("""
                SELECT
                  tc.constraint_name,
                  kcu.column_name,
                  ccu.table_name AS foreign_table_name,
                  ccu.column_name AS foreign_column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON tc.constraint_name = ccu.constraint_name AND tc.table_schema = ccu.constraint_schema
                WHERE tc.constraint_type = 'FOREIGN KEY' AND tc.table_schema = 'public' AND tc.table_name = %s
                  AND kcu.column_name = %s
            """, (table_name, column_name))
            fks = []
            for cname, coln, rtable, rcol in cur.fetchall():
                fks.append({'name': cname, 'columns': [coln], 'ref_table': rtable, 'ref_columns': [rcol]})
            meta['foreign_keys'] = fks

            enum_vals = []
            try:
                udt = meta.get('udt_name')
                if udt:
                    # проверим тип в pg_type: typtype = 'e' (enum)
                    cur.execute("""
                        SELECT t.typtype
                        FROM pg_type t
                        JOIN pg_namespace nsp ON nsp.oid = t.typnamespace
                        WHERE t.typname = %s AND nsp.nspname = 'public'
                        LIMIT 1
                    """, (udt,))
                    trow = cur.fetchone()
                    if trow and trow[0] == 'e':
                        cur.execute("""
                            SELECT e.enumlabel
                            FROM pg_type t
                            JOIN pg_enum e ON t.oid = e.enumtypid
                            WHERE t.typname = %s
                            ORDER BY e.enumsortorder
                        """, (udt,))
                        enum_vals = [r[0] for r in cur.fetchall()]
            except Exception:
                # best-effort, не ломаем основной вывод
                try:
                    logging.exception("Не удалось получить enum values")
                except Exception:
                    pass

            meta['enum_values'] = enum_vals

            try:
                cur.close()
            except Exception:
                pass
            return meta
        except Exception as e:
            logging.exception(f"get_column_metadata error: {e}")
            try:
                cur.close()
            except Exception:
                pass
            return {}

    def _quote_ident(self, name: str) -> str:
        return f'"{name.replace("\"", "\"\"")}"'

    def alter_add_column(self, table: str, column: str, data_type: str,
                         nullable: bool = True, default: Optional[str] = None,
                         unique: bool = False, constraint_name: Optional[str] = None) -> bool:

        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            parts = [f'ALTER TABLE {self._quote_ident(table)} ADD COLUMN {self._quote_ident(column)} {data_type}']
            if default is not None and default != "":
                parts.append(f"DEFAULT %s")
                params = [default]
            else:
                params = []

            if not nullable:
                parts.append("NOT NULL")
            sql = " ".join(parts)
            cur = self.connection.cursor()
            if params:
                cur.execute(sql, tuple(params))
            else:
                cur.execute(sql)
            # unique
            if unique:
                cname = constraint_name or f"uniq_{table}_{column}"
                cur.execute(
                    f"ALTER TABLE {self._quote_ident(table)} ADD CONSTRAINT {self._quote_ident(cname)} UNIQUE ({self._quote_ident(column)})")
            self.connection.commit()
            cur.close()
            try:
                self.mark_structure_changed()
            except Exception:
                pass
            return True
        except Exception as e:
            logging.exception(f"alter_add_column error: {e}")
            try:
                self.connection.rollback()
            except Exception:
                pass
            return False

    def alter_drop_column(self, table: str, column: str, cascade: bool = True) -> bool:

        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            cur = self.connection.cursor()
            sql = f"ALTER TABLE {self._quote_ident(table)} DROP COLUMN {self._quote_ident(column)}"
            if cascade:
                sql += " CASCADE"
            cur.execute(sql)
            self.connection.commit()
            cur.close()
            try:
                self.mark_structure_changed()
            except Exception:
                pass
            return True
        except Exception as e:
            logging.exception(f"alter_drop_column error: {e}")
            try:
                self.connection.rollback()
            except Exception:
                pass
            return False

    def alter_rename_table(self, old_name: str, new_name: str) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            cur = self.connection.cursor()
            cur.execute(f"ALTER TABLE {self._quote_ident(old_name)} RENAME TO {self._quote_ident(new_name)}")
            self.connection.commit()
            cur.close()
            try:
                self.mark_structure_changed()
            except Exception:
                pass
            return True
        except Exception as e:
            logging.exception(f"alter_rename_table error: {e}")
            try:
                self.connection.rollback()
            except Exception:
                pass
            return False

    def alter_rename_column(self, table: str, old_col: str, new_col: str) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            cur = self.connection.cursor()
            cur.execute(
                f"ALTER TABLE {self._quote_ident(table)} RENAME COLUMN {self._quote_ident(old_col)} TO {self._quote_ident(new_col)}")
            self.connection.commit()
            cur.close()
            try:
                self.mark_structure_changed()
            except Exception:
                pass
            return True
        except Exception as e:
            logging.exception(f"alter_rename_column error: {e}")
            try:
                self.connection.rollback()
            except Exception:
                pass
            return False


    def alter_add_constraint(self, table: str, constraint_type: str, details: Dict[str, Any]) -> bool:

        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            cur = self.connection.cursor()
            if constraint_type == 'NOT NULL':
                col = details.get('column')
                cur.execute(f"ALTER TABLE {self._quote_ident(table)} ALTER COLUMN {self._quote_ident(col)} SET NOT NULL")
            elif constraint_type == 'DEFAULT':
                col = details.get('column');
                val = details.get('default')
                cur.execute(f"ALTER TABLE {self._quote_ident(table)} ALTER COLUMN {self._quote_ident(col)} SET DEFAULT %s",
                            (val,))
            elif constraint_type == 'UNIQUE':
                cols = details.get('columns', [])
                cname = details.get('name') or f"uniq_{table}_{'_'.join(cols)}"
                cols_list = ", ".join([self._quote_ident(c) for c in cols])
                cur.execute(
                    f"ALTER TABLE {self._quote_ident(table)} ADD CONSTRAINT {self._quote_ident(cname)} UNIQUE ({cols_list})")
            elif constraint_type == 'CHECK':
                expr = details.get('expr')
                cname = details.get('name') or f"chk_{table}"
                cur.execute(f"ALTER TABLE {self._quote_ident(table)} ADD CONSTRAINT {self._quote_ident(cname)} CHECK ({expr})")
            elif constraint_type == 'FOREIGN KEY':
                cols = details.get('columns', [])
                ref_table = details.get('ref_table')
                ref_cols = details.get('ref_columns', [])
                cname = details.get('name') or f"fk_{table}_{'_'.join(cols)}"
                cols_list = ", ".join([self._quote_ident(c) for c in cols])
                ref_cols_list = ", ".join([self._quote_ident(c) for c in ref_cols])
                cur.execute(
                    f"ALTER TABLE {self._quote_ident(table)} ADD CONSTRAINT {self._quote_ident(cname)} FOREIGN KEY ({cols_list}) REFERENCES {self._quote_ident(ref_table)} ({ref_cols_list})")
            else:
                logging.warning(f"Unknown constraint type: {constraint_type}")
            self.connection.commit()
            cur.close()
            try:
                self.mark_structure_changed()
            except Exception:
                pass
            return True
        except Exception as e:
            logging.exception(f"alter_add_constraint error: {e}")
            try:
                self.connection.rollback()
            except Exception:
                pass
            return False

    def alter_drop_constraint(self, table: str, constraint_name: str) -> bool:
        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            cur = self.connection.cursor()
            cur.execute(f"ALTER TABLE {self._quote_ident(table)} DROP CONSTRAINT {self._quote_ident(constraint_name)} CASCADE")
            self.connection.commit()
            cur.close()
            try:
                self.mark_structure_changed()
            except Exception:
                pass
            return True
        except Exception as e:
            logging.exception(f"alter_drop_constraint error: {e}")
            try:
                self.connection.rollback()
            except Exception:
                pass
            return False

    def clear_column_values(self, table: str, column: str) -> bool:

        try:
            if not self.is_connected():
                if not self.connect():
                    return False
            cur = self.connection.cursor()
            cur.execute(f'UPDATE "{table}" SET "{column}" = NULL')
            self.connection.commit()
            cur.close()
            try:
                self.mark_structure_changed()
            except Exception:
                pass
            return True
        except Exception as e:
            logging.exception(f"clear_column_values error: {e}")
            try:
                self.connection.rollback()
            except Exception:
                pass
            return False

    def alter_change_type(self, table: str, column: str, new_type: str,
                          new_not_null: Optional[bool] = None,
                          new_default: Optional[str] = None,
                          new_unique: Optional[bool] = None,
                          new_fk: Optional[Dict[str, Any]] = None,
                          drop_constraints_first: bool = True) -> (bool, str):

        try:
            if not self.is_connected():
                if not self.connect():
                    return False, "Нет подключения к базе."

            meta = {}
            try:
                meta = self.get_column_metadata(table, column) or {}
            except Exception:
                meta = {}

            cur = self.connection.cursor()

            if drop_constraints_first:
                try:
                    for fk in meta.get('foreign_keys', []) or []:
                        try:
                            cur.execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{fk["name"]}" CASCADE')
                        except Exception:
                            logging.debug("Не удалось удалить FK %s", fk.get('name'))
                    for uq in meta.get('unique_constraints', []) or []:
                        try:
                            cur.execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{uq["name"]}" CASCADE')
                        except Exception:
                            logging.debug("Не удалось удалить UNIQUE %s", uq.get('name'))
                    for chk in meta.get('check_constraints', []) or []:
                        try:
                            cur.execute(f'ALTER TABLE "{table}" DROP CONSTRAINT "{chk["name"]}" CASCADE')
                        except Exception:
                            logging.debug("Не удалось удалить CHECK %s", chk.get('name'))
                    # drop DEFAULT / NOT NULL if present
                    if not meta.get('is_nullable', True):
                        try:
                            cur.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{column}" DROP NOT NULL')
                        except Exception:
                            logging.debug("Не удалось снять NOT NULL")
                    if meta.get('column_default') is not None:
                        try:
                            cur.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{column}" DROP DEFAULT')
                        except Exception:
                            logging.debug("Не удалось снять DEFAULT")
                except Exception:
                    logging.exception("Ошибка при удалении ограничений (best-effort)")

            # Attempt change type
            try:
                # USING expression: "col"::new_type  (без пробела после ::)
                using_expr = f'"{column}"::{new_type}'
                cur.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{column}" TYPE {new_type} USING {using_expr}')
            except Exception as e:
                # Commit nothing, return message so UI может предложить игру очистки колонки
                err = str(e)
                try:
                    cur.close()
                except Exception:
                    pass
                logging.exception("alter_change_type failed: %s", err)
                return False, err

            # Apply new options
            try:
                if new_default is not None:
                    # new_default: raw literal (user must provide correct SQL literal)
                    cur.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{column}" SET DEFAULT {new_default}')
                if new_not_null:
                    cur.execute(f'ALTER TABLE "{table}" ALTER COLUMN "{column}" SET NOT NULL')
                if new_unique:
                    cname = f'uniq_{table}_{column}'
                    cur.execute(f'ALTER TABLE "{table}" ADD CONSTRAINT "{cname}" UNIQUE ("{column}")')
                if new_fk:
                    ref_table = new_fk.get('ref_table')
                    ref_cols = new_fk.get('ref_columns') or []
                    cname = new_fk.get('constraint_name') or f'fk_{table}_{column}'
                    if ref_table and ref_cols:
                        cur.execute(
                            f'ALTER TABLE "{table}" ADD CONSTRAINT "{cname}" FOREIGN KEY ("{column}") REFERENCES "{ref_table}" ("{ref_cols[0]}")')
            except Exception as e:
                try:
                    self.connection.rollback()
                except Exception:
                    pass
                logging.exception("apply post-type-change options failed: %s", e)
                return False, str(e)

            try:
                self.connection.commit()
            except Exception as e:
                logging.exception("commit failed after type change: %s", e)
                return False, str(e)

            try:
                self.mark_structure_changed()
            except Exception:
                pass

            return True, ""

        except Exception as e:  # Добавлен внешний except
            logging.exception("Unexpected error in alter_change_type: %s", e)
            return False, str(e)
        finally:
            try:
                cur.close()
            except Exception:
                pass