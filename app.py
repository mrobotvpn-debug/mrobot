import telebot
import time
import hashlib
import sys
from telebot import types

# 1. КОНФИГУРАЦИЯ
BOT_TOKEN = "8842376879:AAEqSCCPITN9PmG5bRQfYmfeFOiXGUcg_18"
ADMIN_ID = 8414885700
KEY_SECRET = "mrobot_ultra_secret_2024"

bot = telebot.TeleBot(BOT_TOKEN)

def generate_key(days):
    expiry_unix = int(time.time() + (days * 86400))
    expiry_str = str(expiry_unix)
    signature = hashlib.sha256((expiry_str + KEY_SECRET).encode()).hexdigest()[:8]
    return f"MR-{expiry_str}-{signature}"

def get_main_keyboard():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("1д", callback_data="gen_1"),
        types.InlineKeyboardButton("5д", callback_data="gen_5"),
        types.InlineKeyboardButton("7д", callback_data="gen_7"),
        types.InlineKeyboardButton("30д", callback_data="gen_30"),
        types.InlineKeyboardButton("⚙️ Свое число", callback_data="gen_custom")
    )
    return markup

# РЕАКЦИЯ НА ВСЁ
@bot.message_handler(func=lambda m: True)
def handle_all(message):
    print(f"Message from {message.from_user.id}: {message.text}", flush=True)

    if message.text == "/start":
        if message.from_user.id == ADMIN_ID:
            bot.send_message(message.chat.id, "💎 Админ-панель:", reply_markup=get_main_keyboard())
        else:
            bot.send_message(message.chat.id, f"Бот работает. Твой ID: {message.from_user.id}")

    elif message.from_user.id == ADMIN_ID:
        try:
            days = int(message.text.strip())
            key = generate_key(days)
            bot.send_message(message.chat.id, f"✅ Ключ на {days} дн:\n`{key}`", parse_mode="Markdown")
        except:
            bot.send_message(message.chat.id, "Напиши число дней для генерации ключа.")

@bot.callback_query_handler(func=lambda call: True)
def callbacks(call):
    if call.data.startswith("gen_"):
        if call.data == "gen_custom":
            bot.send_message(call.message.chat.id, "Введите число дней.")
        else:
            days = int(call.data.split("_")[1])
            bot.send_message(call.message.chat.id, f"✅ Ключ на {days} дн:\n`{generate_key(days)}`", parse_mode="Markdown")
    bot.answer_callback_query(call.id)

if __name__ == "__main__":
    print("--- ЗАПУСК БОТА ---", flush=True)
    bot.remove_webhook()
    time.sleep(1)
    # Используем infinity_polling для Railway
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
