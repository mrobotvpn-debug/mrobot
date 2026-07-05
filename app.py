import telebot
import time
import hashlib
import logging
from telebot import types

# Настройка логирования (чтобы видеть ошибки в консоли сервера)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# КОНФИГУРАЦИЯ
BOT_TOKEN = "8842376879:AAEqSCCPITN9PmG5bRQfYmfeFOiXGUcg_18"
ADMIN_ID = 8414885700  # Ваш подтвержденный ID
KEY_SECRET = "mrobot_ultra_secret_2024"

bot = telebot.TeleBot(BOT_TOKEN)

# Состояния пользователей
user_states = {}

def generate_key(days):
    """Генерация ключа по алгоритму Mrobot"""
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

@bot.message_handler(commands=['start', 'admin'])
def start_cmd(message):
    logger.info(f"Получена команда /start от {message.from_user.id}")
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            "👋 Привет, Админ! Выберите срок для генерации ключа mrobot:",
            reply_markup=get_main_keyboard()
        )
    else:
        bot.send_message(
            message.chat.id,
            f"❌ Доступ запрещен.\nВаш ID: `{message.from_user.id}`\nСообщите его разработчику.",
            parse_mode="Markdown"
        )

@bot.message_handler(commands=['myid'])
def myid_cmd(message):
    bot.send_message(message.chat.id, f"Ваш Telegram ID: `{message.from_user.id}`", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('gen_'))
def handle_callbacks(call):
    if call.from_user.id != ADMIN_ID:
        return bot.answer_callback_query(call.id, "Нет доступа")

    action = call.data.split('_')[1]

    if action == "custom":
        user_states[call.from_user.id] = "waiting_days"
        bot.send_message(call.message.chat.id, "⌛ Введите количество дней (только число):")
    else:
        days = int(action)
        key = generate_key(days)
        bot.send_message(
            call.message.chat.id,
            f"✅ Ключ mrobot создан на {days} дн.\n\n`{key}`",
            parse_mode="Markdown"
        )
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda message: user_states.get(message.from_user.id) == "waiting_days")
def handle_custom_days(message):
    if message.from_user.id != ADMIN_ID: return

    try:
        days = int(message.text.strip())
        if days <= 0: raise ValueError

        key = generate_key(days)
        bot.send_message(
            message.chat.id,
            f"✅ Ключ mrobot создан на {days} дн.\n\n`{key}`",
            parse_mode="Markdown"
        )
        user_states[message.from_user.id] = None
    except ValueError:
        bot.send_message(message.chat.id, "❌ Ошибка! Введите целое число дней (например, 15).")

@bot.message_handler(func=lambda message: True)
def log_all(message):
    """Логируем все сообщения для отладки"""
    logger.info(f"Сообщение от {message.from_user.id}: {message.text}")
    if message.from_user.id == ADMIN_ID:
        # Если вы просто пишете в бот, это сообщение будет доступно EXE-клиенту как ответ
        pass

if __name__ == "__main__":
    logger.info("--- Бот Mrobot запущен и готов к работе ---")
    bot.polling(none_stop=True, timeout=60)
