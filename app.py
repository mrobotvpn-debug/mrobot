import telebot
import time
import hashlib
import logging
from telebot import types

# Логирование в консоль (проверяйте логи на хостинге!)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

@bot.message_handler(commands=['start'])
def start_handler(message):
    logger.info(f"Command /start from {message.from_user.id}")
    if message.from_user.id == ADMIN_ID:
        bot.send_message(message.chat.id, "💎 Админ-панель Mrobot запущенна.\nВыберите срок ключа:", reply_markup=get_main_keyboard())
    else:
        bot.send_message(message.chat.id, f"🚫 Нет доступа.\nВаш ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.from_user.id != ADMIN_ID: return

    if call.data == "gen_custom":
        msg = bot.send_message(call.message.chat.id, "⌛ Введите количество дней числом:")
        bot.register_next_step_handler(msg, process_custom_days)
    elif call.data.startswith("gen_"):
        days = int(call.data.split("_")[1])
        key = generate_key(days)
        bot.send_message(call.message.chat.id, f"✅ Ключ на {days} дн:\n\n`{key}`", parse_mode="Markdown")

    bot.answer_callback_query(call.id)

def process_custom_days(message):
    try:
        days = int(message.text)
        key = generate_key(days)
        bot.send_message(message.chat.id, f"✅ Ключ на {days} дн:\n\n`{key}`", parse_mode="Markdown")
    except:
        bot.send_message(message.chat.id, "❌ Ошибка. Введите число.")

if __name__ == "__main__":
    try:
        logger.info("Сброс вебхуков...")
        bot.remove_webhook() # Очистка старых сессий
        time.Sleep(1)
        logger.info("Бот запущен. Жду сообщений...")
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
