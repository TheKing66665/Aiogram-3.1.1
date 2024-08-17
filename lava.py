import hmac
import hashlib
import json
import aiohttp
import config as cfg

async def create_lava_invoice(amount, order_id):
    shop_id = cfg.LAVA_SHOP_ID
    secret_key = cfg.LAVA_SECRET_KEY
    
    # Создание данных для запроса
    data = {
        "shopId": shop_id,
        "sum": amount,
        "orderId": order_id,
        "comment": "Оплата через LavaPay",
        "failUrl": "https://example.com/fail",
        "successUrl": "https://example.com/success",
        "hookUrl": "https://example.com/hook",
        "expire": 300
    }

    json_str = json.dumps(data, separators=(',', ':')).encode()

    sign = hmac.new(secret_key.encode('utf-8'), json_str, hashlib.sha256).hexdigest()

    url = 'https://api.lava.ru/business/invoice/create'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Signature': sign
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=json_str, headers=headers) as response:
            data = await response.json()
            if response.status == 200 and data.get('status_check'):
                return data['data']['url'], data['data']['id']
            else:
                print(f"Ошибка при создании инвойса: {data}")
                return None, None

async def check_lava_payment_status(order_id, invoice_id):
    shop_id = cfg.LAVA_SHOP_ID
    secret_key = cfg.LAVA_SECRET_KEY

    data = {
        "orderId": order_id,
        "shopId": shop_id,
        "invoiceId": invoice_id
    }

    json_str = json.dumps(data, separators=(',', ':')).encode()

    sign = hmac.new(secret_key.encode('utf-8'), json_str, hashlib.sha256).hexdigest()

    url = 'https://api.lava.ru/business/invoice/status'
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Signature': sign
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=json_str, headers=headers) as response:
            data = await response.json()
            if response.status == 200 and data.get('status_check'):
                return data['data']['status']
            else:
                print(f"Ошибка при проверке статуса оплаты: {data}")
                return 'error'
