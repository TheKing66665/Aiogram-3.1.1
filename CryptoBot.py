from aiocryptopay import AioCryptoPay, Networks
from states import save_invoice_to_db
import sqlite3
import config as cfg
from aiohttp import web

# Инициализация Aiocryptopay для CryptoBot
crypto = AioCryptoPay(token=cfg.CRYPTO_TOKEN, network=Networks.MAIN_NET)

async def create_crypto_invoice(amount):
    invoice = await crypto.create_invoice(asset='USDT', amount=amount)
    return invoice.bot_invoice_url, invoice.invoice_id

async def handle_crypto_payment(update, app):
    invoice_id = update.invoice_id
    status = update.status

    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE invoices
        SET status = ?
        WHERE invoice_id = ?
    ''', (status, invoice_id))
    conn.commit()
    conn.close()

    print(f"Обновление статуса инвойса: {invoice_id}, статус: {status}")

# Обработчик вебхука для оповещений о платежах через CryptoBot
web_app = web.Application()

@crypto.pay_handler()
async def handle_crypto_payment_webhook(update, app):
    await handle_crypto_payment(update, app)

async def close_session(app):
    await crypto.close()

web_app.add_routes([web.post('/crypto-webhook-path', crypto.get_updates)])
web_app.on_shutdown.append(close_session)
