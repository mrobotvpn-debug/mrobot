import requests
import time
import json
import os
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# Настройки ботов
MAIN_BOT_TOKEN = "8955167157:AAGFP9w7f47DX87u0uBrLIbTpn2Y5MxraTM"
KEYS_BOT_TOKEN = "8982888067:AAFgZ5bCC340zliBSpnYWPIuRUF1NTqOV4o"
ADMIN_CHAT_ID = 8414885700
PORT = int(os.environ.get('PORT', 8080))
DB_FILE = "bot_data.json"

state = {
    "remote_keys": {f"MROBOT-UNI-{i:02d}": 5 for i in range(1, 11)},
    "tested_users": {},
    "key_states": {},
    "last_main_id": 0,
    "last_keys_id": 0,
    "active_user": None
}

def save_db():
    try:
        with open(DB_FILE, "w") as f:
            json.dump({
                "keys": state["remote_keys"], 
                "tested": state["tested_users"],
                "last_main": state["last_main_id"],
                "last_keys": state["last_keys_id"]
            }, f)
    except: pass

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                state["remote_keys"] = data.get("keys", state["remote_keys"])
                state["tested_users"] = data.get("tested", {})
                state["last_main_id"] = data.get("last_main", 0)
                state["last_keys_id"] = data.get("last_keys", 0)
        except: pass

def send(token, chat_id, text, kb=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if kb: payload["reply_markup"] = kb
    try: requests.post(url, json=payload, timeout=10)
    except: pass

class KeyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(state["remote_keys"]).encode())

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), KeyServer)
    print(f"API запущен на порту {PORT}")
    server.serve_forever()

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
                chat_id = msg.get("chat", {}).get("id")
                cb = u.get("callback_query", {})
                if cb: chat_id = cb["from"]["id"]
                if not chat_id: continue
                
                if "successful_payment" in msg:
                    p = msg["successful_payment"]["invoice_payload"]
                    kb = {"inline_keyboard": [[{"text":"ПК", "callback_data":f"plat_pc_{p}"},{"text":"АПК", "callback_data":f"plat_apk_{p}"}]]}
                    send(MAIN_BOT_TOKEN, chat_id, "Оплата принята. Выберите платформу:", json.dumps(kb))
                    continue
                
                if cb:
                    data = cb["data"]
                    if data == "get_test":
                        if str(chat_id) in state["tested_users"]: send(MAIN_BOT_TOKEN, chat_id, "Вы уже брали тест.")
                        else:
                            tk = f"TEST-{chat_id%10000}"
                            state["remote_keys"][tk] = 1
                            state["tested_users"][str(chat_id)] = True
                            save_db()
                            send(MAIN_BOT_TOKEN, chat_id, f"Ваш тестовый ключ на 1 день: `{tk}`")
                    elif data.startswith("buy_"):
                        dur = data.split("_")[1]
                        kb = {"inline_keyboard": [[{"text":"ПК", "callback_data":f"pay_pc_{dur}"},{"text":"АПК", "callback_data":f"pay_apk_{dur}"}]]}
                        send(MAIN_BOT_TOKEN, chat_id, "Выберите устройство:", json.dumps(kb))
                    elif data.startswith("pay_"):
                        p = data.split("_")
                        price = 5 if p[2] == "1d" else 15 if p[2] == "7d" else 40
                        inv = {"chat_id": chat_id, "title": "VPN Mrobot", "description": "Подписка", "payload": f"order_{p[1]}_{p[2]}", "provider_token": "", "currency": "XTR", "prices": [{"label":"Звезды", "amount": price}]}
                        requests.post(f"https://api.telegram.org/bot{MAIN_BOT_TOKEN}/sendInvoice", json=inv)
                    elif data.startswith("plat_"):
                        p = data.split("_")
                        adm_msg = f"НОВЫЙ ЗАКАЗ\nСрок: {p[3]}\nУстройство: {p[1]}\nЮзер: {chat_id}"
                        send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, adm_msg, json.dumps({"inline_keyboard": [[{"text":"Выдать ключ", "callback_data":f"auto_gen_{chat_id}_{p[3]}_{p[1]}"}]]}))
                        send(MAIN_BOT_TOKEN, chat_id, "Заявка отправлена. Ожидайте ключ от админа.")
                    elif data.startswith("set_user_"):
                        state["active_user"] = int(data.split("_")[2])
                        send(MAIN_BOT_TOKEN, chat_id, "Режим ответа пользователю включен.")
                    continue
                
                text = msg.get("text", "")
                if text == "/start":
                    kb = {"inline_keyboard": [[{"text":"ВЗЯТЬ ТЕСТ", "callback_data":"get_test"}],[{"text":"1 день - 5 звезд", "callback_data":"buy_1d"}],[{"text":"7 дней - 15 звезд", "callback_data":"buy_7d"}],[{"text":"30 дней - 40 звезд", "callback_data":"buy_30d"}]]}
                    send(MAIN_BOT_TOKEN, chat_id, "Добро пожаловать в Mrobot VPN! Купите ключ или возьмите тест:", json.dumps(kb))
                elif chat_id == ADMIN_CHAT_ID and state["active_user"]:
                    send(MAIN_BOT_TOKEN, state["active_user"], f"Ответ от поддержки:\n{text}")
                elif text:
                    send(MAIN_BOT_TOKEN, ADMIN_CHAT_ID, f"Сообщение от {chat_id}:\n{text}", json.dumps({"inline_keyboard":[[{"text":"Ответить","callback_data":f"set_user_{chat_id}"}]]}))
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
                chat_id = msg.get("chat", {}).get("id") or cb.get("from", {}).get("id")
                if chat_id != ADMIN_CHAT_ID: continue
                
                if cb:
                    if cb["data"] == "menu_list":
                        txt = "\n".join([f"{k} ({v}дн)" for k,v in state["remote_keys"].items()])
                        send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, f"Активные ключи:\n{txt}")
                    elif cb["data"].startswith("auto_gen_"):
                        state["key_states"][str(chat_id)] = f"send_{cb['data'][9:]}"
                        send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, "Введите ключ для отправки пользователю:")
                    continue
                
                text = msg.get("text", "")
                if text == "/start":
                    send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, "Панель администратора:", json.dumps({"inline_keyboard": [[{"text":"Список ключей", "callback_data":"menu_list"}]]}))
                elif str(chat_id) in state["key_states"]:
                    s = state["key_states"][str(chat_id)]
                    if s.startswith("send_"):
                        tid = s.split("_")[1]
                        state["remote_keys"][text] = 30
                        save_db()
                        send(MAIN_BOT_TOKEN, int(tid), f"Ваш ключ готов: `{text}`")
                        send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, "Ключ успешно отправлен!")
                        del state["key_states"][str(chat_id)]
        except: time.sleep(5)

if __name__ == "__main__":
    load_db()
    Thread(target=poll_main_bot, daemon=True).start()
    Thread(target=run_web_server, daemon=True).start()
    poll_keys_bot()import requests
import time
import json
import os
from threading import Thread
from http.server import BaseHTTPRequestHandler, HTTPServer

# Настройки ботов
MAIN_BOT_TOKEN = "8955167157:AAGFP9w7f47DX87u0uBrLIbTpn2Y5MxraTM"
KEYS_BOT_TOKEN = "8982888067:AAFgZ5bCC340zliBSpnYWPIuRUF1NTqOV4o"
ADMIN_CHAT_ID = 8414885700
PORT = int(os.environ.get('PORT', 8080))
DB_FILE = "bot_data.json"

state = {
    "remote_keys": {f"MROBOT-UNI-{i:02d}": 5 for i in range(1, 11)},
    "tested_users": {},
    "key_states": {},
    "last_main_id": 0,
    "last_keys_id": 0,
    "active_user": None
}

def save_db():
    try:
        with open(DB_FILE, "w") as f:
            json.dump({
                "keys": state["remote_keys"], 
                "tested": state["tested_users"],
                "last_main": state["last_main_id"],
                "last_keys": state["last_keys_id"]
            }, f)
    except: pass

def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                state["remote_keys"] = data.get("keys", state["remote_keys"])
                state["tested_users"] = data.get("tested", {})
                state["last_main_id"] = data.get("last_main", 0)
                state["last_keys_id"] = data.get("last_keys", 0)
        except: pass

def send(token, chat_id, text, kb=None):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if kb: payload["reply_markup"] = kb
    try: requests.post(url, json=payload, timeout=10)
    except: pass

class KeyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(state["remote_keys"]).encode())

def run_web_server():
    server = HTTPServer(('0.0.0.0', PORT), KeyServer)
    print(f"API запущен на порту {PORT}")
    server.serve_forever()

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
                chat_id = msg.get("chat", {}).get("id")
                cb = u.get("callback_query", {})
                if cb: chat_id = cb["from"]["id"]
                if not chat_id: continue
                
                if "successful_payment" in msg:
                    p = msg["successful_payment"]["invoice_payload"]
                    kb = {"inline_keyboard": [[{"text":"ПК", "callback_data":f"plat_pc_{p}"},{"text":"АПК", "callback_data":f"plat_apk_{p}"}]]}
                    send(MAIN_BOT_TOKEN, chat_id, "Оплата принята. Выберите платформу:", json.dumps(kb))
                    continue
                
                if cb:
                    data = cb["data"]
                    if data == "get_test":
                        if str(chat_id) in state["tested_users"]: send(MAIN_BOT_TOKEN, chat_id, "Вы уже брали тест.")
                        else:
                            tk = f"TEST-{chat_id%10000}"
                            state["remote_keys"][tk] = 1
                            state["tested_users"][str(chat_id)] = True
                            save_db()
                            send(MAIN_BOT_TOKEN, chat_id, f"Ваш тестовый ключ на 1 день: `{tk}`")
                    elif data.startswith("buy_"):
                        dur = data.split("_")[1]
                        kb = {"inline_keyboard": [[{"text":"ПК", "callback_data":f"pay_pc_{dur}"},{"text":"АПК", "callback_data":f"pay_apk_{dur}"}]]}
                        send(MAIN_BOT_TOKEN, chat_id, "Выберите устройство:", json.dumps(kb))
                    elif data.startswith("pay_"):
                        p = data.split("_")
                        price = 5 if p[2] == "1d" else 15 if p[2] == "7d" else 40
                        inv = {"chat_id": chat_id, "title": "VPN Mrobot", "description": "Подписка", "payload": f"order_{p[1]}_{p[2]}", "provider_token": "", "currency": "XTR", "prices": [{"label":"Звезды", "amount": price}]}
                        requests.post(f"https://api.telegram.org/bot{MAIN_BOT_TOKEN}/sendInvoice", json=inv)
                    elif data.startswith("plat_"):
                        p = data.split("_")
                        adm_msg = f"НОВЫЙ ЗАКАЗ\nСрок: {p[3]}\nУстройство: {p[1]}\nЮзер: {chat_id}"
                        send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, adm_msg, json.dumps({"inline_keyboard": [[{"text":"Выдать ключ", "callback_data":f"auto_gen_{chat_id}_{p[3]}_{p[1]}"}]]}))
                        send(MAIN_BOT_TOKEN, chat_id, "Заявка отправлена. Ожидайте ключ от админа.")
                    elif data.startswith("set_user_"):
                        state["active_user"] = int(data.split("_")[2])
                        send(MAIN_BOT_TOKEN, chat_id, "Режим ответа пользователю включен.")
                    continue
                
                text = msg.get("text", "")
                if text == "/start":
                    kb = {"inline_keyboard": [[{"text":"ВЗЯТЬ ТЕСТ", "callback_data":"get_test"}],[{"text":"1 день - 5 звезд", "callback_data":"buy_1d"}],[{"text":"7 дней - 15 звезд", "callback_data":"buy_7d"}],[{"text":"30 дней - 40 звезд", "callback_data":"buy_30d"}]]}
                    send(MAIN_BOT_TOKEN, chat_id, "Добро пожаловать в Mrobot VPN! Купите ключ или возьмите тест:", json.dumps(kb))
                elif chat_id == ADMIN_CHAT_ID and state["active_user"]:
                    send(MAIN_BOT_TOKEN, state["active_user"], f"Ответ от поддержки:\n{text}")
                elif text:
                    send(MAIN_BOT_TOKEN, ADMIN_CHAT_ID, f"Сообщение от {chat_id}:\n{text}", json.dumps({"inline_keyboard":[[{"text":"Ответить","callback_data":f"set_user_{chat_id}"}]]}))
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
                chat_id = msg.get("chat", {}).get("id") or cb.get("from", {}).get("id")
                if chat_id != ADMIN_CHAT_ID: continue
                
                if cb:
                    if cb["data"] == "menu_list":
                        txt = "\n".join([f"{k} ({v}дн)" for k,v in state["remote_keys"].items()])
                        send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, f"Активные ключи:\n{txt}")
                    elif cb["data"].startswith("auto_gen_"):
                        state["key_states"][str(chat_id)] = f"send_{cb['data'][9:]}"
                        send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, "Введите ключ для отправки пользователю:")
                    continue
                
                text = msg.get("text", "")
                if text == "/start":
                    send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, "Панель администратора:", json.dumps({"inline_keyboard": [[{"text":"Список ключей", "callback_data":"menu_list"}]]}))
                elif str(chat_id) in state["key_states"]:
                    s = state["key_states"][str(chat_id)]
                    if s.startswith("send_"):
                        tid = s.split("_")[1]
                        state["remote_keys"][text] = 30
                        save_db()
                        send(MAIN_BOT_TOKEN, int(tid), f"Ваш ключ готов: `{text}`")
                        send(KEYS_BOT_TOKEN, ADMIN_CHAT_ID, "Ключ успешно отправлен!")
                        del state["key_states"][str(chat_id)]
        except: time.sleep(5)

if __name__ == "__main__":
    load_db()
    Thread(target=poll_main_bot, daemon=True).start()
    Thread(target=run_web_server, daemon=True).start()
    poll_keys_bot()