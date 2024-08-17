import hashlib
import uuid
from AaioAPI import AsyncAaioAPI
import config as cfg
import asyncio

def create_signature(order_id, amount, currency):
    signature_string = f"{cfg.API_KEY}:{amount}:{currency}:{cfg.SECRET_KEY}:{order_id}"
    signature = hashlib.sha256(signature_string.encode('utf-8')).hexdigest()
    return signature

async def create_payment(amount, currency='RUB', description='Пополнение через AAIO'):
    client = AsyncAaioAPI(cfg.API_KEY, cfg.SECRET_KEY, cfg.API_KEY)

    order_id = str(uuid.uuid4())  # Генерация уникального ID заказа
    lang = 'ru'

    try:
        signature = create_signature(order_id, amount, currency)
        URL = await client.create_payment(order_id, amount, lang, currency, description)
        return URL, order_id
    except Exception as e:
        print(f"Ошибка при создании платежа: {e}")
        return None, None

async def check_payment_status(order_id):
    client = AsyncAaioAPI(cfg.API_KEY, cfg.SECRET_KEY, cfg.API_KEY)

    try:
        expired = await asyncio.wait_for(client.is_expired(order_id), timeout=10)
        success = await asyncio.wait_for(client.is_success(order_id), timeout=10)

        if expired:
            return 'expired'
        elif success:
            return 'paid'
        else:
            return 'pending'
    except asyncio.TimeoutError:
        print(f"Тайм-аут при проверке статуса оплаты для order_id: {order_id}")
        return 'timeout'
    except Exception as e:
        print(f"Ошибка при проверке статуса оплаты: {e}")
        return 'error'
