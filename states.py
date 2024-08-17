from aiogram.fsm.state import State, StatesGroup
import sqlite3

class PaymentStates(StatesGroup):
    waiting_for_amount_aaio = State()
    waiting_for_amount_crypto = State()
    waiting_for_amount_lava = State()
    waiting_for_amount_crystalpay = State()

def save_invoice_to_db(chat_id, asset, amount, invoice_id, status, order_id, payment_method):
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO invoices (chat_id, asset, amount, invoice_id, status, order_id, payment_method)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (chat_id, asset, amount, invoice_id, status, order_id, payment_method))
    conn.commit()
    conn.close()

# Функция для создания таблицы базы данных, если она не существует
def init_db():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id INTEGER,
            asset TEXT,
            amount REAL,
            invoice_id TEXT,
            status TEXT,
            order_id TEXT,
            payment_method TEXT
        )
    ''')
    conn.commit()
    conn.close()
