import telebot
import time
import hashlib
from telebot import types

# Конфигурация
BOT_TOKEN = "8842376879:AAEqSCCPITN9PmG5bRQfYmfeFOiXGUcg_18"
ADMIN_ID = 8414885700
KEY_SECRET = "mrobot_ultra_secret_2024"

bot = telebot.TeleBot(BOT_TOKEN)

# Состояние для ввода своего числа дней
user_states = {}

def generate_key(days):
    """Генерация ключа по алгоритму Mrobot"""
    expiry_unix = int(time.time() + (days * 86400))
    expiry_str = str(expiry_unix)

    # Создание подписи
    sign_src = expiry_str + KEY_SECRET
    signature = hashlib.sha256(sign_src.encode()).hexdigest()[:8]

    return f"MR-{expiry_str}-{signature}"

def get_main_keyboard():
    """Клавиатура как на скриншоте"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("1д", callback_data="gen_1")
    btn5 = types.InlineKeyboardButton("5д", callback_data="gen_5")
    btn7 = types.InlineKeyboardButton("7д", callback_data="gen_7")
    btn30 = types.InlineKeyboardButton("30д", callback_data="gen_30")
    btn_custom = types.InlineKeyboardButton("⚙️ Свое число", callback_data="gen_custom")

    markup.add(btn1, btn5, btn7, btn30)
    markup.add(btn_custom)
    return markup

@bot.message_handler(commands=['start', 'admin'])
def start_cmd(message):
    if message.from_user.id == ADMIN_ID:
        bot.send_message(
            message.chat.id,
            "Выберите срок для mrobot:",
            reply_markup=get_main_keyboard()
        )
    else:
        bot.send_message(message.chat.id, "У вас нет доступа к управлению.")

@bot.callback_query_handler(func=lambda call: call.data.startswith('gen_'))
def handle_callbacks(call):
    if call.from_user.id != ADMIN_ID: return

    action = call.data.split('_')[1]

    if action == "custom":
        user_states[call.from_user.id] = "waiting_days"
        bot.send_message(call.message.chat.id, "⌛ Введите количество дней числом:")
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
        days = int(message.text)
        if days <= 0: raise ValueError

        key = generate_key(days)
        bot.send_message(
            message.chat.id,
            f"✅ Ключ mrobot создан на {days} дн.\n\n`{key}`",
            parse_mode="Markdown"
        )
        user_states[message.from_user.id] = None
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите корректное число дней.")

@bot.message_handler(func=lambda message: True)
def handle_support(message):
    """Обработка ответов пользователям (если сообщение не команда)"""
    if message.from_user.id == ADMIN_ID:
        # Здесь можно добавить логику пересылки ответа конкретному пользователю,
        # но так как в VPN приложении используется polling GetSupportReplies,
        # админу достаточно просто написать текст в чат бота, и клиент его увидит.
        print(f"Админ ответил: {message.text}")

if __name__ == "__main__":
    print("Бот Mrobot запущен...")
    bot.polling(none_stop=True)
