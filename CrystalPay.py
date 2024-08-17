import requests
import config as cfg

def create_crystalpay_invoice(amount, description, invoice_type='purchase'):
    url = "https://api.crystalpay.io/v2/invoice/create/"
    payload = {
        "auth_login": cfg.CRYSTALPAY_LOGIN,
        "auth_secret": cfg.CRYSTALPAY_SECRET,
        "amount": amount,
        "type": invoice_type,
        "description": description,
        "redirect_url": "https://example.com/success",  # Замените на реальный URL
        "callback_url": "https://example.com/callback",  # Замените на реальный URL
        "lifetime": 1440  # 24 часа
    }
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if data.get("error"):
        print(f"Ошибка при создании инвойса CrystalPay: {data.get('errors')}")
        return None, None
    return data.get("url"), data.get("id")


def check_crystalpay_payment_status(invoice_id):
    url = "https://api.crystalpay.io/v2/invoice/info/"
    payload = {
        "auth_login": cfg.CRYSTALPAY_LOGIN,
        "auth_secret": cfg.CRYSTALPAY_SECRET,
        "id": invoice_id
    }
    headers = {'Content-Type': 'application/json'}

    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    if data.get("error"):
        print(f"Ошибка при проверке статуса оплаты CrystalPay: {data.get('errors')}")
        return 'error'
    
    return data.get("state")
