import telebot
import time
import hashlib
from telebot import types

# ТОКЕН И КОНФИГ
BOT_TOKEN = "8842376879:AAEqSCCPITN9PmG5bRQfYmfeFOiXGUcg_18"
ADMIN_ID = 8414885700
KEY_SECRET = "mrobot_ultra_secret_2024"

bot = telebot.TeleBot(BOT_TOKEN)

def generate_key(days):
    expiry_unix = int(time.time() + (days * 86400))
    expiry_str = str(expiry_unix)
    sign_src = expiry_str + KEY_SECRET
    signature = hashlib.sha256(sign_src.encode()).hexdigest()[:8]
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

# РЕАГИРУЕТ НА ВСЁ (ДЛЯ ТЕСТА)
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    print(f"Получено сообщение от {message.from_user.id}: {message.text}")

    if message.text == "/start" or message.text == "/admin":
        if message.from_user.id == ADMIN_ID:
            bot.send_message(message.chat.id, "💎 Админ-панель запущенна:", reply_markup=get_main_keyboard())
        else:
            bot.send_message(message.chat.id, f"Привет! Бот работает.\nТвой ID: `{message.from_user.id}`", parse_mode="Markdown")

    elif message.from_user.id == ADMIN_ID:
        # Если вы просто пишете число, бот сделает ключ
        try:
            days = int(message.text)
            key = generate_key(days)
            bot.send_message(message.chat.id, f"✅ Ключ на {days} дн:\n\n`{key}`", parse_mode="Markdown")
        except:
            bot.send_message(message.chat.id, "Напишите /start для меню или число дней для ключа.")

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data.startswith("gen_"):
        if call.data == "gen_custom":
            bot.send_message(call.message.chat.id, "Введите количество дней числом:")
        else:
            days = int(call.data.split("_")[1])
            key = generate_key(days)
            bot.send_message(call.message.chat.id, f"✅ Ключ на {days} дн:\n\n`{key}`", parse_mode="Markdown")
    bot.answer_callback_query(call.id)

if __name__ == "__main__":
    print("--- ТЕСТОВЫЙ ЗАПУСК БОТА ---")
    try:
        bot.remove_webhook()
        time.sleep(1)
        print("Бот слушает... Напишите ему в Telegram!")
        bot.infinity_polling()
    except Exception as e:
        print(f"Ошибка при запуске: {e}")
