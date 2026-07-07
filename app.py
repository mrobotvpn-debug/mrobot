import telebot
import time
import hashlib
import os
import threading
from telebot import types

# --- КОНФИГУРАЦИЯ ---
TOKEN_PURCHASE = "8955167157:AAGFP9w7f47DX87u0uBrLIbTpn2Y5MxraTM"
TOKEN_GENERATOR = "8982888067:AAFgZ5bCC340zliBSpnYWPIuRUF1NTqOV4o"

ADMIN_ID = 8414885700
KEY_SECRET = "mrobot_ultra_secret_2024"

# Инициализация ботов
bot_purchase = telebot.TeleBot(TOKEN_PURCHASE)
bot_generator = telebot.TeleBot(TOKEN_GENERATOR)

# --- ФУНКЦИИ ГЕНЕРАЦИИ ---
def generate_key(days):
    expiry_unix = int(time.time() + (days * 86400))
    expiry_str = str(expiry_unix)
    signature = hashlib.sha256((expiry_str + KEY_SECRET).encode()).hexdigest()[:8]
    return f"MR-{expiry_str}-{signature}"

# --- ЛОГИКА БОТА ПОКУПКИ (С ПОДДЕРЖКОЙ ЗВЕЗД) ---

@bot_purchase.message_handler(commands=['start'])
def start_purchase(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    # Кнопки оплаты звездами
    star_prices = [5, 15, 25, 30, 40, 50, 100, 200]
    btns = [types.InlineKeyboardButton(f"🌟 {p} звёзд", callback_data=f"buy_stars_{p}") for p in star_prices]

    markup.add(*btns)
    markup.add(types.InlineKeyboardButton("👨‍💻 Поддержка", url="https://t.me/Moderat0rs"))

    bot_purchase.send_message(
        message.chat.id,
        "👋 Привет! Выбери количество звёзд для покупки подписки VPN Mrobot:",
        reply_markup=markup
    )

@bot_purchase.callback_query_handler(func=lambda call: call.data.startswith("buy_stars_"))
def handle_star_payment(call):
    amount = int(call.data.split("_")[2])

    # Определяем на сколько дней подписка в зависимости от звезд (примерная логика)
    days_map = {5: 1, 15: 3, 25: 7, 30: 10, 40: 14, 50: 30, 100: 90, 200: 365}
    days = days_map.get(amount, 1)

    prices = [types.LabeledPrice(label=f"Подписка {days} дн.", amount=amount)]

    bot_purchase.send_invoice(
        call.message.chat.id,
        title=f"VPN Mrobot - {days} дн.",
        description=f"Доступ к VPN на {days} дней. Оплата звездами Telegram.",
        provider_token="", # Пусто для Telegram Stars
        currency="XTR",
        prices=prices,
        invoice_payload=f"payload_days_{days}",
        start_parameter="vpn-sub"
    )
    bot_purchase.answer_callback_query(call.id)

@bot_purchase.pre_checkout_query_handler(func=lambda query: True)
def checkout(pre_checkout_query):
    bot_purchase.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@bot_purchase.message_handler(content_types=['successful_payment'])
def got_payment(message):
    payload = message.successful_payment.invoice_payload
    days = int(payload.split("_")[2])

    # Генерируем ключ автоматически после оплаты
    key = generate_key(days)

    bot_purchase.send_message(
        message.chat.id,
        f"✅ Оплата прошла успешно!\n\nТвой ключ на {days} дн:\n`{key}`\n\nИспользуй его в приложении EXE или APK.",
        parse_mode="Markdown"
    )

    # Уведомляем админа
    bot_purchase.send_message(ADMIN_ID, f"💰 Новая покупка!\nЮзер: {message.from_user.id}\nДней: {days}\nЗвёзд: {message.successful_payment.total_amount}")

# --- ЛОГИКА БОТА ГЕНЕРАЦИИ ---
def get_gen_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("1 день", callback_data="gen_1"),
        types.InlineKeyboardButton("30 дней", callback_data="gen_30"),
        types.InlineKeyboardButton("90 дней", callback_data="gen_90"),
        types.InlineKeyboardButton("365 дней", callback_data="gen_365")
    )
    return markup

@bot_generator.message_handler(commands=['start'])
def start_generator(message):
    if message.from_user.id == ADMIN_ID:
        bot_generator.send_message(message.chat.id, "💎 Панель генерации ключей Mrobot (EXE/APK):", reply_markup=get_gen_keyboard())
    else:
        bot_generator.send_message(message.chat.id, "❌ У вас нет доступа.")

@bot_generator.callback_query_handler(func=lambda call: True)
def handle_gen_callback(call):
    if call.data.startswith("gen_") and call.from_user.id == ADMIN_ID:
        days = int(call.data.split("_")[1])
        key = generate_key(days)
        bot_generator.send_message(call.message.chat.id, f"✅ Ключ на {days} дн:\n`{key}`", parse_mode="Markdown")
    bot_generator.answer_callback_query(call.id)

# --- ЗАПУСК ---
if __name__ == "__main__":
    def run_purchase():
        print("Бот ПОКУПКИ запущен (Stars Active)...")
        bot_purchase.infinity_polling(timeout=10, long_polling_timeout=5)

    def run_generator():
        print("Бот ГЕНЕРАЦИИ запущен...")
        bot_generator.infinity_polling(timeout=10, long_polling_timeout=5)

    t1 = threading.Thread(target=run_purchase)
    t2 = threading.Thread(target=run_generator)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
