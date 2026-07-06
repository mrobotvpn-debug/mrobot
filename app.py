import telebot
import time
import hashlib
import logging
import sys
from telebot import types

# 1. НАСТРОЙКА ЛОГОВ (Смотрите их в панели хостинга!)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# 2. КОНФИГУРАЦИЯ
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

# 3. ОБРАБОТЧИК ВСЕХ СООБЩЕНИЙ
@bot.message_handler(func=lambda message: True)
def handle_all_messages(message):
    user_id = message.from_user.id
    text = message.text
    logger.info(f"Получено сообщение от {user_id}: {text}")

    if text == "/start" or text == "/admin":
        if user_id == ADMIN_ID:
            bot.send_message(message.chat.id, "💎 Админ-панель Mrobot запущенна.\nВыберите срок ключа:", reply_markup=get_main_keyboard())
        else:
            bot.send_message(message.chat.id, f"Привет! Бот работает.\nТвой ID: `{user_id}`\nДоступа к генерации ключей нет.", parse_mode="Markdown")

    elif user_id == ADMIN_ID:
        try:
            days = int(text.strip())
            key = generate_key(days)
            bot.send_message(message.chat.id, f"✅ Ключ на {days} дн:\n\n`{key}`", parse_mode="Markdown")
        except ValueError:
            bot.send_message(message.chat.id, "Команда не распознана. Введите число дней или /start")

# 4. ОБРАБОТЧИК КНОПОК
@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "Нет доступа")

    if call.data == "gen_custom":
        bot.send_message(call.message.chat.id, "⌛ Введите количество дней числом (просто отправьте сообщение):")
    elif call.data.startswith("gen_"):
        days = int(call.data.split("_")[1])
        key = generate_key(days)
        bot.send_message(call.message.chat.id, f"✅ Ключ на {days} дн:\n\n`{key}`", parse_mode="Markdown")

    bot.answer_callback_query(call.id)

# 5. ЗАПУСК
if __name__ == "__main__":
    logger.info("Удаление старых вебхуков...")
    bot.remove_webhook()
    time.sleep(1)
    logger.info("Бот запускает бесконечный опрос (polling)...")
    try:
        bot.infinity_polling(timeout=20, long_polling_timeout=10)
    except Exception as e:
        logger.error(f"Ошибка при работе: {e}")
        time.sleep(5)
