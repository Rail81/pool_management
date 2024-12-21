import unittest
import sqlite3
from datetime import datetime, timedelta
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestPoolManagementBot(unittest.TestCase):
    def setUp(self):
        # Создаем тестовую базу данных
        self.conn = sqlite3.connect(':memory:')
        self.cursor = self.conn.cursor()
        
        # Создаем необходимые таблицы
        self.cursor.executescript('''
        CREATE TABLE client (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            telegram_id TEXT UNIQUE NOT NULL,
            subscription_balance INTEGER DEFAULT 0
        );
        
        CREATE TABLE daily_slots (
            id INTEGER PRIMARY KEY,
            date TEXT NOT NULL,
            total_slots INTEGER NOT NULL,
            available_slots INTEGER NOT NULL
        );
        
        CREATE TABLE visit (
            id INTEGER PRIMARY KEY,
            client_id INTEGER NOT NULL,
            visit_date TEXT NOT NULL,
            FOREIGN KEY(client_id) REFERENCES client(id)
        );
        
        CREATE TABLE subscription_log (
            id INTEGER PRIMARY KEY,
            client_id INTEGER NOT NULL,
            action TEXT NOT NULL,
            amount INTEGER NOT NULL,
            date TEXT NOT NULL,
            FOREIGN KEY(client_id) REFERENCES client(id)
        );
        ''')
        
        # Подготовка тестовых данных
        self.cursor.execute('''
        INSERT INTO client (name, phone, telegram_id, subscription_balance) 
        VALUES (?, ?, ?, ?)
        ''', ('Тестовый Клиент', '+79001234567', '123456', 5))
        
        self.cursor.execute('''
        INSERT INTO daily_slots (date, total_slots, available_slots) 
        VALUES (?, ?, ?)
        ''', (datetime.now().strftime('%Y-%m-%d'), 10, 5))
        
        self.conn.commit()

    def tearDown(self):
        # Закрываем соединение с базой данных
        self.conn.close()

    def test_book_slot_successful(self):
        # Получаем ID клиента и слота
        self.cursor.execute('SELECT id FROM client WHERE telegram_id = ?', ('123456',))
        client_id = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT id FROM daily_slots WHERE available_slots > 0')
        slot_id = self.cursor.fetchone()[0]
        
        # Имитируем бронирование
        self.cursor.execute(
            'UPDATE daily_slots SET available_slots = available_slots - 1 WHERE id = ?',
            (slot_id,)
        )
        
        self.cursor.execute(
            'UPDATE client SET subscription_balance = subscription_balance - 1 WHERE id = ?',
            (client_id,)
        )
        
        self.cursor.execute(
            'INSERT INTO visit (client_id, visit_date) VALUES (?, ?)',
            (client_id, datetime.now().strftime('%Y-%m-%d'))
        )
        
        self.cursor.execute(
            'INSERT INTO subscription_log (client_id, action, amount, date) VALUES (?, ?, ?, ?)',
            (client_id, 'списание', 1, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        )
        
        self.conn.commit()
        
        # Проверяем результаты
        self.cursor.execute('SELECT subscription_balance FROM client WHERE id = ?', (client_id,))
        remaining_balance = self.cursor.fetchone()[0]
        self.assertEqual(remaining_balance, 4, "Баланс абонемента должен уменьшиться на 1")
        
        self.cursor.execute('SELECT available_slots FROM daily_slots WHERE id = ?', (slot_id,))
        available_slots = self.cursor.fetchone()[0]
        self.assertEqual(available_slots, 4, "Количество доступных слотов должно уменьшиться на 1")
        
        # Проверяем логирование
        self.cursor.execute('SELECT * FROM subscription_log WHERE client_id = ?', (client_id,))
        logs = self.cursor.fetchall()
        self.assertTrue(len(logs) > 0, "Должна быть запись в логе списания")
        
        # Проверяем визит
        self.cursor.execute('SELECT * FROM visit WHERE client_id = ?', (client_id,))
        visits = self.cursor.fetchall()
        self.assertTrue(len(visits) > 0, "Должна быть создана запись о визите")

    def test_book_slot_no_balance(self):
        # Создаем клиента без баланса
        self.cursor.execute('''
        INSERT INTO client (name, phone, telegram_id, subscription_balance) 
        VALUES (?, ?, ?, ?)
        ''', ('Клиент Без Баланса', '+79007654321', '654321', 0))
        self.conn.commit()
        
        # Получаем ID клиента и слота
        self.cursor.execute('SELECT id FROM client WHERE telegram_id = ?', ('654321',))
        client_id = self.cursor.fetchone()[0]
        
        self.cursor.execute('SELECT id FROM daily_slots WHERE available_slots > 0')
        slot_id = self.cursor.fetchone()[0]
        
        # Проверяем, что нельзя списать баланс
        self.cursor.execute('SELECT subscription_balance FROM client WHERE id = ?', (client_id,))
        balance_before = self.cursor.fetchone()[0]
        
        try:
            self.cursor.execute(
                'UPDATE client SET subscription_balance = subscription_balance - 1 WHERE id = ? AND subscription_balance > 0',
                (client_id,)
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
        
        self.cursor.execute('SELECT subscription_balance FROM client WHERE id = ?', (client_id,))
        balance_after = self.cursor.fetchone()[0]
        
        self.assertEqual(balance_before, balance_after, "Баланс не должен меняться при нулевом балансе")

    def test_book_slot_no_available_slots(self):
        # Получаем ID клиента
        self.cursor.execute('SELECT id FROM client WHERE telegram_id = ?', ('123456',))
        client_id = self.cursor.fetchone()[0]
        
        # Обнуляем доступные слоты
        self.cursor.execute('UPDATE daily_slots SET available_slots = 0')
        self.conn.commit()
        
        # Получаем ID слота
        self.cursor.execute('SELECT id FROM daily_slots')
        slot_id = self.cursor.fetchone()[0]
        
        # Проверяем, что нельзя забронировать слот
        self.cursor.execute('SELECT available_slots FROM daily_slots WHERE id = ?', (slot_id,))
        slots_before = self.cursor.fetchone()[0]
        
        try:
            self.cursor.execute(
                'UPDATE daily_slots SET available_slots = available_slots - 1 WHERE id = ? AND available_slots > 0',
                (slot_id,)
            )
            self.conn.commit()
        except Exception:
            self.conn.rollback()
        
        self.cursor.execute('SELECT available_slots FROM daily_slots WHERE id = ?', (slot_id,))
        slots_after = self.cursor.fetchone()[0]
        
        self.assertEqual(slots_before, slots_after, "Количество слотов не должно меняться при отсутствии доступных мест")

if __name__ == '__main__':
    unittest.main()
