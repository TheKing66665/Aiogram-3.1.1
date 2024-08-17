import asyncio
import sqlite3
import uuid
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from config import BOT_TOKEN
from states import PaymentStates, save_invoice_to_db, init_db

import CryptoBot
import CrystalPay
import aaio
import lava

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Инициализация базы данных при запуске
init_db()

# Команда /start
@dp.message(Command("start"))
async def send_welcome(message: types.Message):
    payment_markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Пополнить AAIO", callback_data="topup_aaio")],
        [InlineKeyboardButton(text="Пополнить CryptoBot", callback_data="topup_crypto")],
        [InlineKeyboardButton(text="Пополнить LavaPay", callback_data="topup_lava")],
        [InlineKeyboardButton(text="Пополнить CrystalPay", callback_data="topup_crystalpay")]
    ])
    await message.answer("Выберите способ пополнения:", reply_markup=payment_markup)

# Обработка нажатия на кнопку "Пополнить AAIO"
@dp.callback_query(F.data == "topup_aaio")
async def process_topup_aaio(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите сумму для пополнения через AAIO:")
    await state.set_state(PaymentStates.waiting_for_amount_aaio)

# Обработка ввода суммы и создание платежа через AaioAPI
@dp.message(PaymentStates.waiting_for_amount_aaio)
async def process_amount_aaio(message: types.Message, state: FSMContext):
    try:
        amount = int(message.text)
        payment_url, order_id = await aaio.create_payment(amount)

        if payment_url:
            payment_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='💳 Оплатить через AAIO', url=payment_url)],
                [InlineKeyboardButton(text='🔄 Проверить оплату', callback_data=f'check_payment:{order_id}')]
            ])
            await message.answer(f"Вы собираетесь оплатить {amount} рублей через AAIO. Нажмите кнопку ниже для оплаты.", reply_markup=payment_markup)
            await state.clear()
        else:
            await message.answer("Произошла ошибка при создании ссылки для оплаты. Пожалуйста, попробуйте позже.")
            await state.clear()
    except ValueError:
        await message.answer("Введите корректное число.")

# Проверка статуса оплаты через AaioAPI
@dp.callback_query(F.data.startswith('check_payment'))
async def check_payment(callback_query: types.CallbackQuery):
    _, order_id = callback_query.data.split(':')
    try:
        payment_status = await aaio.check_payment_status(order_id)
        if payment_status == 'paid':
            await callback_query.message.answer('✅ Оплата через AAIO успешно завершена! Спасибо за покупку!')
            await callback_query.message.edit_reply_markup()
        elif payment_status == 'expired':
            await callback_query.message.answer('❌ Счет через AAIO просрочен. Пожалуйста, создайте новый заказ.')
        elif payment_status == 'pending':
            await callback_query.message.answer('⏳ Оплата через AAIO находится в процессе. Пожалуйста, подождите.')
        elif payment_status == 'timeout':
            await callback_query.message.answer('❌ Время ожидания ответа через AAIO истекло. Пожалуйста, попробуйте позже.')
        else:
            await callback_query.message.answer('❌ Оплата через AAIO не завершена или произошла ошибка. Пожалуйста, попробуйте позже.')
    except Exception as e:
        print(f"Ошибка при проверке статуса оплаты: {e}")
        await callback_query.message.answer('❌ Произошла ошибка при проверке статуса оплаты через AAIO. Попробуйте позже.')

# Обработка нажатия на кнопку "Пополнить CryptoBot"
@dp.callback_query(F.data == "topup_crypto")
async def process_topup_crypto(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите сумму для пополнения через CryptoBot:")
    await state.set_state(PaymentStates.waiting_for_amount_crypto)

# Обработка ввода суммы и создание инвойса через CryptoBot
@dp.message(PaymentStates.waiting_for_amount_crypto)
async def process_amount_crypto(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        invoice_url, invoice_id = await CryptoBot.create_crypto_invoice(amount)

        save_invoice_to_db(message.chat.id, 'USDT', amount, invoice_id, 'pending', '', 'CryptoBot')

        payment_markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='💳 Оплатить через CryptoBot', url=invoice_url)],
            [InlineKeyboardButton(text='🔄 Проверить оплату', callback_data=f'check_crypto_payment:{invoice_id}')]
        ])
        await message.answer(f"Вы собираетесь оплатить {amount} USDT через CryptoBot. Нажмите кнопку ниже для оплаты.", reply_markup=payment_markup)
        await state.clear()
    except ValueError:
        await message.answer("Введите корректное число.")

# Проверка статуса оплаты через CryptoBot
@dp.callback_query(F.data.startswith('check_crypto_payment'))
async def check_crypto_payment(callback_query: types.CallbackQuery):
    invoice_id = callback_query.data.split(':')[-1]

    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT status FROM invoices WHERE invoice_id = ?', (invoice_id,))
    result = cursor.fetchone()
    conn.close()

    if result:
        status = result[0]
        await callback_query.answer(f"Статус оплаты через CryptoBot: {status}")
    else:
        await callback_query.answer("Инвойс не найден")

# Обработка нажатия на кнопку "Пополнить LavaPay"
@dp.callback_query(F.data == "topup_lava")
async def process_topup_lava(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите сумму для пополнения через LavaPay:")
    await state.set_state(PaymentStates.waiting_for_amount_lava)

# Обработка ввода суммы и создание инвойса через LavaPay
@dp.message(PaymentStates.waiting_for_amount_lava)
async def process_amount_lava(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        order_id = str(uuid.uuid4())
        payment_url, invoice_id = await lava.create_lava_invoice(amount, order_id)

        if payment_url:
            save_invoice_to_db(message.chat.id, 'LavaPay', amount, invoice_id, 'pending', order_id, 'LavaPay')

            callback_data = f'check_lava:{order_id[:8]}:{invoice_id[:8]}'
            payment_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='💳 Оплатить через LavaPay', url=payment_url)],
                [InlineKeyboardButton(text='🔄 Проверить оплату', callback_data=callback_data)]
            ])
            await message.answer(f"Вы собираетесь оплатить {amount} через LavaPay. Нажмите кнопку ниже для оплаты.", reply_markup=payment_markup)
            await state.clear()
        else:
            await message.answer("Произошла ошибка при создании ссылки для оплаты. Пожалуйста, попробуйте позже.")
            await state.clear()
    except ValueError:
        await message.answer("Введите корректное число.")

# Проверка статуса оплаты через LavaPay
@dp.callback_query(F.data.startswith('check_lava'))
async def check_lava_payment(callback_query: types.CallbackQuery):
    try:
        _, short_order_id, short_invoice_id = callback_query.data.split(':')
        
        conn = sqlite3.connect('invoices.db')
        cursor = conn.cursor()
        cursor.execute('SELECT order_id, invoice_id FROM invoices WHERE order_id LIKE ? AND invoice_id LIKE ?', 
                       (f'{short_order_id}%', f'{short_invoice_id}%'))
        result = cursor.fetchone()
        conn.close()

        if not result:
            await callback_query.message.answer("Не удалось найти инвойс. Пожалуйста, попробуйте позже.")
            return
        
        order_id, invoice_id = result

        payment_status = await lava.check_lava_payment_status(order_id, invoice_id)

        if payment_status == 'paid':
            await callback_query.message.answer('✅ Оплата через LavaPay успешно завершена! Спасибо за покупку!')
            await callback_query.message.edit_reply_markup()
        elif payment_status == 'created':
            await callback_query.message.answer('⏳ Оплата через LavaPay находится в процессе. Пожалуйста, подождите.')
        else:
            await callback_query.message.answer('❌ Оплата через LavaPay не завершена или произошла ошибка. Пожалуйста, попробуйте позже.')

    except Exception as e:
        print(f"Ошибка при проверке статуса оплаты: {e}")
        await callback_query.message.answer('❌ Произошла ошибка при проверке статуса оплаты через LavaPay. Попробуйте позже.')

# Обработка нажатия на кнопку "Пополнить CrystalPay"
@dp.callback_query(F.data == "topup_crystalpay")
async def process_topup_crystalpay(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.message.answer("Введите сумму для пополнения через CrystalPay:")
    await state.set_state(PaymentStates.waiting_for_amount_crystalpay)

# Обработка ввода суммы и создание инвойса через CrystalPay
@dp.message(PaymentStates.waiting_for_amount_crystalpay)
async def process_amount_crystalpay(message: types.Message, state: FSMContext):
    try:
        amount = float(message.text.strip())
        description = "Пополнение через CrystalPay"
        payment_url, invoice_id = CrystalPay.create_crystalpay_invoice(amount, description)

        if payment_url:
            save_invoice_to_db(message.chat.id, 'CrystalPay', amount, invoice_id, 'pending', invoice_id, 'CrystalPay')

            payment_markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='💳 Оплатить через CrystalPay', url=payment_url)],
                [InlineKeyboardButton(text='🔄 Проверить оплату', callback_data=f'check_crystalpay:{invoice_id}')]
            ])
            await message.answer(f"Вы собираетесь оплатить {amount} через CrystalPay. Нажмите кнопку ниже для оплаты.", reply_markup=payment_markup)
            await state.clear()
        else:
            await message.answer("Произошла ошибка при создании ссылки для оплаты. Пожалуйста, попробуйте позже.")
            await state.clear()
    except ValueError:
        await message.answer("Введите корректное число.")

# Проверка статуса оплаты через CrystalPay
@dp.callback_query(F.data.startswith('check_crystalpay'))
async def check_crystalpay_payment(callback_query: types.CallbackQuery):
    invoice_id = callback_query.data.split(':')[-1]

    payment_status = CrystalPay.check_crystalpay_payment_status(invoice_id)
    
    if payment_status == 'payed':
        await callback_query.message.answer('✅ Оплата через CrystalPay успешно завершена! Спасибо за покупку!')
        await callback_query.message.edit_reply_markup()
    elif payment_status == 'notpayed':
        await callback_query.message.answer('⏳ Оплата через CrystalPay находится в процессе. Пожалуйста, подождите.')
    else:
        await callback_query.message.answer('❌ Оплата через CrystalPay не завершена или произошла ошибка. Пожалуйста, попробуйте позже.')

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
