import requests
import time
import json
import os
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# Настройки ботов
MAIN_BOT_TOKEN = "8955167157:AAGFP9w7f47DX87u0uBrLIbTpn2Y5MxraTM"
KEYS_BOT_TOKEN = "8982888067:AAFgZ5bCC340zliBSpnYWPIuRUF1NTqOV4o"
SUPPORT_BOT_TOKEN = "8842376879:AAEqSCCPITN9PmG5bRQfYmfeFOiXGUcg_18" # Тот самый бот для техподдержки
ADMIN_CHAT_ID = 8414885700
PORT = int(os.environ.get('PORT', 8080))
DB_FILE = "bot_data.json"
APK_KEYS_FILE = "C:\\Users\\человек паук\\Desktop\\test ddos\\apk_keys.txt"

state = {
    "remote_keys": {f"MROBOT-UNI-{i:02d}": 5 for i in range(1, 11)},
    "tested_users": {},
    "key_states": {},
    "last_main_id": 0,
    "last_keys_id": 0,
    "last_support_id": 0,
    "active_user": None
}

def save_db():
    try:
        with open(DB_FILE, "w") as f:
            json.dump(state, f)
        # Синхронизация с файлом для АПК
        with open(APK_KEYS_FILE, "w") as f:
            for k, v in state["remote_keys"].items():
                f.write(f"{k}:{v}\n")
    except Exception as e:
        print(f"Ошибка сохранения: {e}")

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                state.update(data)
                print("БД загружена")
        except: pass

def send(token, chat_id, text, kb=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if kb:
        payload["reply_markup"] = kb if isinstance(kb, dict) else json.loads(kb)
    try:
        requests.post(url, json=payload, timeout=10)
    except: pass

class KeyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(state["remote_keys"]).encode())

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), KeyServer)
    print(f"API сервер запущен на порту {PORT}")
    server.serve_forever()

def get_duration_kb():
    return {
        "inline_keyboard": [
            [{"text": "1д", "callback_data": "days_1"}, {"text": "5д", "callback_data": "days_5"}],
            [{"text": "7д", "callback_data": "days_7"}, {"text": "30д", "callback_data": "days_30"}],
            [{"text": "⚙️ Свое число", "callback_data": "days_custom"}]
        ]
    }

def poll_main_bot():
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{MAIN_BOT_TOKEN}/getUpdates?offset={state['last_main_id']+1}&timeout=30", timeout=35).json()
            for u in r.get("result", []):
                state["last_main_id"] = u["update_id"]
                save_db()
                if "pre_checkout_query" in u:
                    requests.get(f"https://api.telegram.org/bot{MAIN_BOT_TOKEN}/answerPreCheckoutQuery?pre_checkout_query_id={u['pre_checkout_query']['id']}&ok=true")
                    continue

                msg = u.get("message", {})
                cb = u.get("callback_query", {})
                chat_id = msg.get("chat", {}).get("id") if msg else cb.get("from", {}).get("id")
                if not chat_id: continue

                if "successful_payment" in msg:
                    p = msg["successful_payment"]["invoice_payload"]
                    kb = {"inline_keyboard": [[{"text":"ПК", "callback_data":f"plat_pc_{p}"},{"text":"АПК", "callback_data":f"plat_apk_{p}"}]]}
                    send(MAIN_BOT_TOKEN, chat_id, "✅ Оплачено! Выберите платформу:", kb)
                    continue

                if cb:
                    data = cb["data"]
                    if data == "get_test":
                        if str(chat_id) in state["tested_users"]:
                            send(MAIN_BOT_TOKEN, chat_id, "❌ Вы уже брали тест!")
                        else:
                            tk = f"TEST-{chat_id%10000}"
                            state["remote_keys"][tk] = 1
                            state["tested_users"][str(chat_id)] = True
                            save_db()
                            send(MAIN_BOT_TOKEN, chat_id, f"🎁 Ваш тестовый ключ на 1 день: `{tk}`")
                    elif data.startswith("buy_"):
                        dur = data.split("_")[1]
                        kb = {"inline_keyboard": [[{"text":"💻 ПК", "callback_data":f"pay_pc_{dur}"},{"text":"📱 АПК", "callback_data":f"pay_apk_{dur}"}]]}
                        send(MAIN_BOT_TOKEN, chat_id, "Выберите устройство:", kb)
                    elif data.startswith("pay_"):
                        p = data.split("_")
                        price = 5 if p[2] == "1d" else 15 if p[2] == "7d" else 40
                        inv = {"chat_id": chat_id, "title": "VPN Mrobot", "description": "Подписка", "payload": f"order_{p[1]}_{p[2]}", "provider_token": "", "currency": "XTR", "prices": [{"label":"Stars", "amount": price}]}
                        requests.post(f"https://api.telegram.org/bot{MAIN_BOT_TOKEN}/sendInvoice", json=inv)
                    elif data.startswith("plat_"):
                        p = data.split("_")
                        adm_msg = f"💰 ЗАЯВКА\nСрок: {p[3]}\nУстройство: {p[1]}\nЮзер: {chat_id}"
                        send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, adm_msg, {"inline_keyboard": [[{"text":"🔑 Создать","callback_data":f"auto_gen_{chat_id}_{p[3]}_{p[1]}"}]]})
                        send(MAIN_BOT_TOKEN, chat_id, "✅ Заявка отправлена. Ожидайте ключ!")
                    continue

                text = msg.get("text", "")
                if text == "/start":
                    kb = {"inline_keyboard": [[{"text":"🎁 ВЗЯТЬ ТЕСТ", "callback_data":"get_test"}],[{"text":"1д - 5⭐", "callback_data":"buy_1d"}],[{"text":"7д - 15⭐", "callback_data":"buy_7d"}],[{"text":"30д - 40⭐", "callback_data":"buy_30d"}]]}
                    send(MAIN_BOT_TOKEN, chat_id, "👋 Добро пожаловать! Купите ключ или возьмите тест:", kb)
                elif text:
                    # Сообщения из основного бота в поддержку
                    kb = {"inline_keyboard":[[{"text":"Ответить","callback_data":f"set_user_{chat_id}"}]]}
                    send(SUPPORT_BOT_TOKEN, ADMIN_CHAT_ID, f"📩 Основной Бот - Сообщение от {chat_id}:\n{text}", kb)
        except: time.sleep(5)

def poll_support_bot():
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{SUPPORT_BOT_TOKEN}/getUpdates?offset={state['last_support_id']+1}&timeout=30", timeout=35).json()
            for u in r.get("result", []):
                state["last_support_id"] = u["update_id"]
                save_db()
                cb = u.get("callback_query", {})
                msg = u.get("message", {})
                chat_id = msg.get("chat", {}).get("id") if msg else cb.get("from", {}).get("id")

                if cb:
                    data = cb["data"]
                    if data.startswith("set_user_"):
                        state["active_user"] = int(data.split("_")[2])
                        send(SUPPORT_BOT_TOKEN, chat_id, f"💬 Режим ответа юзеру {state['active_user']} включен.")
                    continue

                text = msg.get("text", "")
                if chat_id == ADMIN_CHAT_ID and state["active_user"]:
                    # Ответ админа из бота поддержки летит в основной бот пользователю
                    send(MAIN_BOT_TOKEN, state["active_user"], f"📩 Ответ от поддержки:\n{text}")
                    send(SUPPORT_BOT_TOKEN, chat_id, "✅ Отправлено пользователю.")
                elif text and chat_id != ADMIN_CHAT_ID:
                    # Прямые сообщения в бот поддержки
                    kb = {"inline_keyboard":[[{"text":"Ответить","callback_data":f"set_user_{chat_id}"}]]}
                    send(SUPPORT_BOT_TOKEN, ADMIN_CHAT_ID, f"📩 Поддержка - Сообщение от {chat_id}:\n{text}", kb)
        except: time.sleep(5)

def poll_keys_bot():
    while True:
        try:
            r = requests.get(f"https://api.telegram.org/bot{KEYS_BOT_TOKEN}/getUpdates?offset={state['last_keys_id']+1}&timeout=30", timeout=35).json()
            for u in r.get("result", []):
                state["last_keys_id"] = u["update_id"]
                save_db()
                cb = u.get("callback_query", {})
                msg = u.get("message", {})
                chat_id = msg.get("chat", {}).get("id") if msg else cb.get("from", {}).get("id")

                if chat_id != ADMIN_CHAT_ID: continue

                if cb:
                    data = cb["data"]
                    sid = str(chat_id)
                    if data == "menu_create":
                        send(KEYS_BOT_TOKEN, chat_id, "📝 Введите название нового ключа:")
                        state["key_states"][sid] = "creating_manual"
                    elif data == "menu_delete":
                        send(KEYS_BOT_TOKEN, chat_id, "🗑 Введите название ключа для удаления:")
                        state["key_states"][sid] = "awaiting_delete"
                    elif data == "menu_list":
                        keys = state["remote_keys"]
                        msg_text = "📋 Список ключей:\n" + "\n".join([f"• `{k}` ({v} дн.)" for k, v in keys.items()])
                        send(KEYS_BOT_TOKEN, chat_id, msg_text)
                    elif data == "menu_issue":
                        send(KEYS_BOT_TOKEN, chat_id, "🎫 Введите ID пользователя:")
                        state["key_states"][sid] = "awaiting_issue_id"
                    elif data == "days_custom":
                        curr_state = state["key_states"].get(sid, "")
                        if curr_state.startswith("key_for_"):
                            state["key_states"][sid] = "custom_days_for_" + curr_state[8:]
                            send(KEYS_BOT_TOKEN, chat_id, "⏳ Введите количество дней числом:")
                        elif curr_state.startswith("issue_key_"):
                            state["key_states"][sid] = "custom_days_issue_" + curr_state[10:]
                            send(KEYS_BOT_TOKEN, chat_id, "⏳ Введите количество дней числом:")
                    elif data.startswith("days_"):
                        days = int(data.split("_")[1])
                        curr_state = state["key_states"].get(sid, "")
                        if curr_state.startswith("key_for_"):
                            key = curr_state[8:]
                            state["remote_keys"][key] = days
                            save_db()
                            send(KEYS_BOT_TOKEN, chat_id, f"✅ Ключ `{key}` создан на {days} дн.")
                            del state["key_states"][sid]
                        elif curr_state.startswith("issue_key_"):
                            target_id = int(curr_state[10:])
                            key = f"MROBOT-{target_id%1000}-{int(time.time()%1000)}"
                            state["remote_keys"][key] = days
                            save_db()
                            send(MAIN_BOT_TOKEN, target_id, f"🎁 Админ выдал вам ключ: `{key}` ({days} дн.)")
                            send(KEYS_BOT_TOKEN, chat_id, f"✅ Ключ `{key}` отправлен пользователю {target_id}!")
                            del state["key_states"][sid]
                    elif data.startswith("auto_gen_"):
                        parts = data.split("_")
                        state["key_states"][sid] = f"send_to_{parts[2]}_{parts[3]}_{parts[4]}"
                        send(KEYS_BOT_TOKEN, chat_id, "📝 Введите текст ключа для отправки:")
                    elif data.startswith("confirm_send_"):
                        p = data.split("_")
                        target_id = int(p[2])
                        key = p[5]
                        days = int(p[3].replace("d", ""))
                        state["remote_keys"][key] = days
                        save_db()
                        send(MAIN_BOT_TOKEN, target_id, f"🎁 Ваш ключ готов: `{key}` ({days} дн.)")
                        send(KEYS_BOT_TOKEN, chat_id, "✅ Ключ успешно отправлен!")
                        del state["key_states"][sid]
                    continue

                text = msg.get("text", "")
                sid = str(chat_id)
                if text == "/start":
                    kb = {"inline_keyboard": [[{"text":"➕ Создать","callback_data":"menu_create"},{"text":"🗑 Удалить","callback_data":"menu_delete"}],[{"text":"📋 Список","callback_data":"menu_list"},{"text":"🎫 Выдать","callback_data":"menu_issue"}]]}
                    send(KEYS_BOT_TOKEN, chat_id, "👋 Админ-панель:", kb)
                elif sid in state["key_states"]:
                    curr = state["key_states"][sid]
                    if curr == "creating_manual":
                        state["key_states"][sid] = "key_for_" + text
                        send(KEYS_BOT_TOKEN, chat_id, f"Выберите срок для `{text}`:", get_duration_kb())
                    elif curr == "awaiting_delete":
                        if text in state["remote_keys"]:
                            del state["remote_keys"][text]
                            save_db()
                            send(KEYS_BOT_TOKEN, chat_id, "🗑 Удалено.")
                        else: send(KEYS_BOT_TOKEN, chat_id, "❌ Не найден.")
                        del state["key_states"][sid]
                    elif curr == "awaiting_issue_id":
                        try:
                            target_id = int(text)
                            state["key_states"][sid] = f"issue_key_{target_id}"
                            send(KEYS_BOT_TOKEN, chat_id, f"Выберите срок для пользователя {target_id}:", get_duration_kb())
                        except: send(KEYS_BOT_TOKEN, chat_id, "❌ Введите числовой ID.")
                    elif curr.startswith("custom_days_for_"):
                        try:
                            days = int(text)
                            key = curr[16:]
                            state["remote_keys"][key] = days
                            save_db()
                            send(KEYS_BOT_TOKEN, chat_id, f"✅ Ключ `{key}` создан на {days} дн.")
                            del state["key_states"][sid]
                        except: send(KEYS_BOT_TOKEN, chat_id, "❌ Введите число.")
                    elif curr.startswith("custom_days_issue_"):
                        try:
                            days = int(text)
                            target_id = int(curr[18:])
                            key = f"MROBOT-{target_id%1000}-{int(time.time()%1000)}"
                            state["remote_keys"][key] = days
                            save_db()
                            send(MAIN_BOT_TOKEN, target_id, f"🎁 Админ выдал вам ключ: `{key}` ({days} дн.)")
                            send(KEYS_BOT_TOKEN, chat_id, f"✅ Ключ `{key}` выдан!")
                            del state["key_states"][sid]
                        except: send(KEYS_BOT_TOKEN, chat_id, "❌ Введите число.")
                    elif curr.startswith("send_to_"):
                        p = curr.split("_")
                        kb = {"inline_keyboard": [[{"text": "✅ ПОДТВЕРДИТЬ", "callback_data": f"confirm_send_{p[2]}_{p[3]}_{p[4]}_{text}"}]]}
                        send(KEYS_BOT_TOKEN, chat_id, f"Отправить `{text}` пользователю {p[2]}?", kb)
        except: time.sleep(5)

if __name__ == "__main__":
    load_db()
    Thread(target=poll_main_bot, daemon=True).start()
    Thread(target=poll_support_bot, daemon=True).start() # Добавлен опрос бота поддержки
    Thread(target=run_web_server, daemon=True).start()
    poll_keys_bot()
