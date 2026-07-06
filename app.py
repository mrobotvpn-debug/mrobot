import telebot
import time
import hashlib
import os
from telebot import types

# --- КОНФИГУРАЦИЯ ---
# Токены ботов
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

# --- ЛОГИКА БОТА ПОКУПКИ ---
@bot_purchase.message_handler(commands=['start'])
def start_purchase(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("Купить ключ (1 мес) - 300₽", url="https://t.me/your_payment_link")
    btn2 = types.InlineKeyboardButton("Поддержка", url="https://t.me/человек паук")
    markup.add(btn1)
    markup.add(btn2)
    bot_purchase.send_message(message.chat.id, "👋 Привет! Здесь ты можешь купить ключи для VPN Mrobot (EXE/APK).", reply_markup=markup)

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
    import threading

    def run_purchase():
        print("Бот ПОКУПКИ запущен...")
        bot_purchase.infinity_polling(timeout=10, long_polling_timeout=5)

    def run_generator():
        print("Бот ГЕНЕРАЦИИ запущен...")
        bot_generator.infinity_polling(timeout=10, long_polling_timeout=5)

    # Запускаем обоих ботов в разных потоках для Railway
    t1 = threading.Thread(target=run_purchase)
    t2 = threading.Thread(target=run_generator)

    t1.start()
    t2.start()

    t1.join()
    t2.join()
