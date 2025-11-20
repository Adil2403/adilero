import os
import json
import requests
import sqlite3
import telebot
from telebot import types
from datetime import datetime
from typing import Tuple, Optional

from aiohttp import web

async def handle(request):
    return web.Response(text="Bot is running")

app = web.Application()
app.add_routes([web.get('/', handle)])

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=10000)


bot = telebot.TeleBot('8424828219:AAH_7OzBaKGY0wxgJOqERKguugjzkhLjmFg')    
GROQ_API_KEY = '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'
@bot.message_handler(commands=['help', 'start'])
def main (message):
    help_text= (
        "Привет! Я CS2 Bot, твой помощник по Counter-Strike 2.\n\n"
        "Вот что я умею:\n"
        "- Отвечать на вопросы о CS2 (игра, скины, механики и т.д.)\n"
        "- Предоставлять информацию о скинах и их ценах\n"
        "- Запоминать полезные ответы для будущих запросов\n\n"
        "Просто задай мне вопрос, и я постараюсь помочь!"
    )
    bot.send_message(message.chat.id, help_text)
DB_FILE = "questions.db"
REACTIONS_DIR = "reactions"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = "llama-3.3-70b-versatile"
MAX_DISLIKES = 3


bot = telebot.TeleBot('8424828219:AAH_7OzBaKGY0wxgJOqERKguugjzkhLjmFg')
ai_contexts = {}  

def get_db_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)

def init_db_and_seed():
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS qa (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT UNIQUE,
                    answer TEXT,
                    type TEXT,
                    reaction TEXT
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    age INTEGER,
                    city TEXT,
                    chat_id INTEGER UNIQUE
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question TEXT,
                    answer TEXT,
                    user_id INTEGER,
                    liked INTEGER,
                    ts INTEGER
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS ai_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uid TEXT,
                    question TEXT,
                    answer TEXT,
                    user_id INTEGER,
                    success INTEGER,
                    error TEXT,
                    ts INTEGER
                )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    question TEXT,
                    timestamp TEXT
                )""")
    conn.commit()

    cur.execute("SELECT COUNT(*) FROM qa")
    if cur.fetchone()[0] < 50:
        sample = [
            ("что такое cs2", "Counter-Strike 2 — обновлённая версия CS:GO на Source 2.", "text", "reactions/smile.png"),
            ("cs2 вышла в каком году", "CS2 вышла в 2023 году.", "text", "reactions/smile.png"),
            ("cs2 бесплатна", "Да", "yes_no", "reactions/smile.png"),
            ("играют ли в cs2 много людей", "Да", "yes_no", "reactions/happy.png"),
            ("как повысить фпс", "Снизь настройки графики, отключи тени и VSync, обнови драйверы.", "text", "reactions/thinking.png"),
            ("что такое float", "Float — показатель износа скина от 0.00 до 1.00.", "text", "reactions/info.png"),
            ("что такое stattrak", "StatTrak — счётчик убийств на предмете.", "text", "reactions/info.png"),
            ("как получить нож", "Нож можно получить из кейсов, купить на маркете или через трейд.", "text", "reactions/wow.png"),
            ("что такое contraband", "Contraband — редкая категория скинов, пример: Howl.", "text", "reactions/rare.png"),
            ("что такое souvenir", "Souvenir — сувенирные скины с турниров.", "text", "reactions/rare.png"),
            ("есть ли премиум в cs2", "Нет", "yes_no", "reactions/sad.png"),
            ("что значит kato", "Это стикеры Katowice; некоторые версии очень дорогие.", "text", "reactions/info.png"),
            ("как проверить float", "Используй сторонние сайты по float или расширения.", "text", "reactions/info.png"),
            ("какие бывают состояния", "Factory New, Minimal Wear, Field-Tested, Well-Worn, Battle-Scarred.", "text", "reactions/info.png"),
            ("как торговать безопасно", "Проверяй профиль партнёра и отзывы, используй трейд-офферы.", "text", "reactions/thinking.png"),
            ("сколько стоит awp asiimov", "Цена зависит от состояния; уточни состояние.", "text", "reactions/info.png"),
            ("какая редкость howl", "Contraband", "text", "reactions/rare.png"),
            ("как вывести деньги со скинов", "Прямого вывода нет — используются обмены и сторонние сервисы (риск).", "text", "reactions/warning.png"),
            ("где посмотреть историю цен", "На странице предмета в Steam Market или на сторонних сайтах.", "text", "reactions/info.png"),
            ("что такое trade-up", "Обмен 10 предметов одной редкости на случайный предмет более высокой.", "text", "reactions/info.png"),
            ("что такое doppler", "Doppler — фазы окраса, влияет на цену ножей.", "text", "reactions/info.png"),
            ("как улучшить прицел", "Тренируйся на тренировочных картах и настрой чувствительность.", "text", "reactions/happy.png"),
            ("есть ли античит", "Valve Anti-Cheat (VAC) и внутриигровые меры.", "text", "reactions/info.png"),
            ("как узнать float ножа", "Проверяй float на страницах предмета или сторонних сайтах.", "text", "reactions/info.png"),
            ("factory new что значит", "Factory New — минимальный износ (лучшее состояние).", "text", "reactions/info.png"),
            ("где купить дешево", "На сторонних площадках иногда дешевле — будь осторожен.", "text", "reactions/warning.png"),
            ("какие скины в тренде", "Популярны Asiimov, Howl, Doppler-ножи, Dragon Lore — зависит от спроса.", "text", "reactions/happy.png"),
            ("сколько стоит howl m4a4", "Цена сильно варьируется; укажи состояние.", "text", "reactions/info.png"),
            ("что такое pattern index", "Индекс паттерна — вариация рисунка у скинов.", "text", "reactions/info.png"),
            ("как создать trade offer", "Через профиль → Сделки → Отправить предложение обмена.", "text", "reactions/info.png"),
            ("когда выйдет новая операция", "Информации нет — следи за официальными анонсами.", "text", "reactions/thinking.png"),
            ("что такое souvenir package", "Набор сувенирных предметов с турниров.", "text", "reactions/info.png"),
            ("как проверить честность торговца", "Смотри профиль, историю, отзывы и возраст аккаунта.", "text", "reactions/info.png"),
            ("что такое meme float", "Очень низкий float (например 0.000x) — особенно ценится.", "text", "reactions/rare.png"),
            ("что такое pattern", "Паттерн — визуальная вариация текстуры предмета.", "text", "reactions/info.png"),
            ("сколько времени вывод на steam", "После продажи средства появляются в кошельке Steam согласно правилам.", "text", "reactions/info.png"),
            ("как получить souvenir", "Сувенирные предметы получают с сувенирных пакетов турниров.", "text", "reactions/info.png"),
            ("что такое autographed", "Автографы игроков на предметах, обычно повышают ценность.", "text", "reactions/info.png"),
            ("какие ножи самые дорогие", "Karambit, M9 Bayonet, Butterfly — дорогие модели в определённых паттернах.", "text", "reactions/wow.png"),
            ("как проверить редкость", "Редкость указана на странице предмета и в описании.", "text", "reactions/info.png"),
            ("что такое stattrak счетчик", "Счётчик убийств на предмете (StatTrak).", "text", "reactions/info.png"),
            ("как заработать скины", "Через игры, кейсы, трейды и торговлю на рынке.", "text", "reactions/happy.png"),
            ("что такое crimson web", "Crimson Web — паттерн с характерной сеткой.", "text", "reactions/info.png"),
        ]
        while len(sample) < 50:
            sample.append((f"вопрос {len(sample)+1}", f"ответ {len(sample)+1}", "text", "reactions/smile.png"))
        cur.executemany("INSERT OR IGNORE INTO qa (question, answer, type, reaction) VALUES (?, ?, ?, ?)", sample)
        conn.commit()
    conn.close()

init_db_and_seed()

def search_qa_exact(question: str):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT answer, type, reaction FROM qa WHERE LOWER(question)=?", (question.lower(),))
    row = cur.fetchone()
    conn.close()
    return row

def search_qa_fuzzy(question: str, cutoff=0.6):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT question FROM qa")
    rows = [r[0] for r in cur.fetchall()]
    conn.close()
    import difflib
    match = difflib.get_close_matches(question, rows, n=1, cutoff=cutoff)
    return match[0] if match else None

def log_query(user_id:int, text:str):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO logs (user_id, question, timestamp) VALUES (?, ?, ?)",
                (user_id, text, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def save_feedback(question, answer, user_id, liked):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO feedback (question, answer, user_id, liked, ts) VALUES (?, ?, ?, ?, ?)",
                (question, answer, user_id, liked, int(datetime.now().timestamp())))
    conn.commit()
    conn.close()

def save_to_qa(question, answer, reaction=""):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT OR IGNORE INTO qa (question, answer, type, reaction) VALUES (?, ?, ?, ?)",
                (question, answer, "text", reaction))
    conn.commit()
    conn.close()

def log_ai_call(uid, question, answer, user_id, success, error_text=None):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO ai_log (uid, question, answer, user_id, success, error, ts) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (uid, question, answer if answer else "", user_id, 1 if success else 0, error_text if error_text else "", int(datetime.now().timestamp())))
    conn.commit()
    conn.close()

def get_skin_info(skin_name: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    base_url = "https://steamcommunity.com/market/priceoverview/"
    search_url = "https://steamcommunity.com/market/search/render/"
    params = {"appid": 730, "query": skin_name, "norender": 1, "count": 5}
    try:
        r = requests.get(search_url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("results"):
                first = data["results"][0]
                real_name = first["hash_name"]
                price_params = {"currency": 5, "appid": 730, "market_hash_name": real_name}
                pr = requests.get(base_url, params=price_params, timeout=10)
                if pr.status_code == 200:
                    pd = pr.json()
                    if pd.get("success"):
                        price = pd.get("lowest_price", "Нет данных")
                        link = f"https://steamcommunity.com/market/listings/730/{real_name.replace(' ', '%20')}"
                        return real_name, price, link
        return None, None, None
    except Exception as e:
        print("Steam API error:", e)
        return None, None, None

@bot.message_handler(commands=['skin'])
def cmd_skin(message):
    bot.send_message(message.chat.id, "Введите название скина (например: AWP | Asiimov).")
    bot.register_next_step_handler(message, process_skin_name)

def process_skin_name(message):
    chat_id = message.chat.id
    skin_name = message.text.strip()
    if not skin_name:
        bot.send_message(chat_id, "Название скина пустое. Попробуйте ещё раз командой /skin.")
        return
    msg = bot.send_message(chat_id, f"Ищу информацию по: {skin_name} ...")
    try:
        real_name, price, link = get_skin_info(skin_name)
        if real_name:
            resp = f"Найден: {real_name}\nЦена: {price}\nСсылка: {link}"
        else:
            resp = "Скин не найден. Попробуйте точнее указать название (например: 'AWP | Asiimov')."
        bot.edit_message_text(resp, chat_id, msg.message_id)
    except Exception as e:
        print("process_skin_name error:", e)
        try:
            bot.edit_message_text("Ошибка при поиске скина. Попробуйте позже.", chat_id, msg.message_id)
        except:
            bot.send_message(chat_id, "Ошибка при поиске скина. Попробуйте позже.")

def ask_groq(question: str) -> Tuple[bool, str, Optional[str]]:
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": "Ты — умный Telegram-бот, специализируешься на игре CS 2, но при желании юзера можешь так же поговорить по душам на обычную тему, как обычный ИИ."},
            {"role": "user", "content": question}
        ],
        "temperature": 0.7
    }
    try:
        resp = requests.post(GROQ_URL, headers=headers, json=payload, timeout=20)
        if resp.status_code == 200:
            j = resp.json()
            try:
                ans = j["choices"][0]["message"]["content"].strip()
            except Exception:
                ans = str(j)
            return True, ans, None
        else:
            return False, "", f"{resp.status_code} - {resp.text}"
    except Exception as e:
        return False, "", str(e)

def make_feedback_kb(uid: str):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(" Понравился ответ", callback_data=f"fb|{uid}|1"))
    kb.add(types.InlineKeyboardButton(" Не понравился ответ", callback_data=f"fb|{uid}|0"))
    return kb

def make_yesno_keyboard():
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    kb.add("Да", "Нет")
    return kb

def start_registration(message):
    bot.send_message(message.chat.id, "Привет! Как тебя зовут?")
    bot.register_next_step_handler(message, reg_get_name)

def reg_get_name(message):
    name = message.text.strip()
    bot.send_message(message.chat.id, "Сколько тебе лет? (введите число)")
    bot.register_next_step_handler(message, reg_get_age, name)

def reg_get_age(message, name):
    age = message.text.strip()
    if not age.isdigit():
        bot.send_message(message.chat.id, "Возраст должен быть числом, введи снова:")
        bot.register_next_step_handler(message, reg_get_age, name)
        return
    bot.send_message(message.chat.id, "Из какого ты города?")
    bot.register_next_step_handler(message, reg_get_city, name, int(age))

def reg_get_city(message, name, age):
    city = message.text.strip()
    conn = get_db_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT OR REPLACE INTO users (name, age, city, chat_id) VALUES (?, ?, ?, ?)", (name, age, city, message.chat.id))
        conn.commit()
    except Exception as e:
        print("DB error (register):", e)
    finally:
        conn.close()
    bot.send_message(message.chat.id, f"Приятно познакомиться, {name}! Теперь задавай вопросы — я буду обращаться к тебе по имени.")

@bot.message_handler(commands=['start'])
def cmd_start(message):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT name FROM users WHERE chat_id=?", (message.chat.id,))
    row = cur.fetchone()
    conn.close()
    if row:
        bot.send_message(message.chat.id, f"С возвращением, {row[0]}! Можешь задавать вопросы.")
    else:
        start_registration(message)

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    text = message.text.strip()
    chat_id = message.chat.id
    log_query(chat_id, text)

    qa_row = search_qa_exact(text)
    if qa_row:
        answer, qtype, reaction = qa_row
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT name FROM users WHERE chat_id=?", (chat_id,))
        row = cur.fetchone()
        conn.close()
        name = row[0] if row else "Игрок"
        if qtype == "yes_no":
            bot.send_message(chat_id, f"{name}, {answer}", reply_markup=make_yesno_keyboard())
        else:
            bot.send_message(chat_id, f"{name}, {answer}")
        if reaction and os.path.exists(reaction):
            try:
                with open(reaction, "rb") as img:
                    bot.send_photo(chat_id, img)
            except Exception as e:
                print("Send reaction image error:", e)
        return

    fuzzy = search_qa_fuzzy(text)
    if fuzzy:
        conn = get_db_conn()
        cur = conn.cursor()
        cur.execute("SELECT answer FROM qa WHERE question=?", (fuzzy,))
        r = cur.fetchone()
        conn.close()
        if r:
            bot.send_message(chat_id, f"(Найден похожий вопрос: {fuzzy})\n{r[0]}")
            return

    uid = str(datetime.now().timestamp()).replace(".", "") + "_" + str(chat_id)
    ai_contexts[uid] = {"question": text, "last_answer": None, "user_id": chat_id, "attempts": 0, "ts": datetime.now().timestamp()}

    success, ans, err = ask_groq(text)
    log_ai_call(uid, text, ans if ans else "", chat_id, success, err)
    if not success:
        bot.send_message(chat_id, " Не удалось получить ответ от AI. Попробуй позже.")
        ai_contexts.pop(uid, None)
        return

    ai_contexts[uid]["last_answer"] = ans
    ai_contexts[uid]["attempts"] = 0
    bot.send_message(chat_id, ans, reply_markup=make_feedback_kb(uid))

@bot.callback_query_handler(func=lambda call: call.data.startswith("fb|"))
def handle_feedback(call):
    try:
        _, uid, liked_s = call.data.split("|")
        liked = int(liked_s)
        ctx = ai_contexts.get(uid)
        if not ctx:
            bot.answer_callback_query(call.id, "Контекст устарел или недоступен.")
            return
        question = ctx["question"]
        last_answer = ctx["last_answer"]
        user_id = ctx["user_id"]
        attempts = ctx["attempts"]

        if liked == 1:
            save_to_qa(question, last_answer)
            save_feedback(question, last_answer, user_id, 1)
            bot.answer_callback_query(call.id, "Спасибо! Ответ сохранён в базе.")
            bot.send_message(user_id, "Спасибо за отзыв! Этот ответ добавлен в базу знаний.")
            ai_contexts.pop(uid, None)
            return

        save_feedback(question, last_answer, user_id, 0)
        attempts += 1
        ctx["attempts"] = attempts

        if attempts >= MAX_DISLIKES:
            bot.answer_callback_query(call.id, "Достигнут предел попыток. Обратитесь к оператору.")
            bot.send_message(user_id, "К сожалению, не удалось подобрать подходящий ответ. Пожалуйста, обратитесь к оператору.")
            ai_contexts.pop(uid, None)
            return

        bot.answer_callback_query(call.id, "Получено. Попробую переформулировать ответ.")
        clar = f"Переформулируй, сделай ответ короче и понятнее для обычного пользователя.\n\nВопрос: {question}\n\nПоследний ответ: {last_answer}"
        success, new_ans, err = ask_groq(clar)
        log_ai_call(uid, question, new_ans if new_ans else "", user_id, success, err)
        if not success:
            bot.send_message(user_id, "Ошибка при обращении к AI. Попробуй позже.")
            ai_contexts.pop(uid, None)
            return
        ctx["last_answer"] = new_ans
        ai_contexts[uid] = ctx
        bot.send_message(user_id, f"Попробую иначе (попытка {attempts}/{MAX_DISLIKES}):\n\n{new_ans}", reply_markup=make_feedback_kb(uid))
    except Exception as e:
        print("callback error:", e)
        try:
            bot.answer_callback_query(call.id, "Внутренняя ошибка.")
        except:
            pass

@bot.message_handler(commands=['logs'])
def cmd_logs(message):
    conn = get_db_conn()
    cur = conn.cursor()
    cur.execute("SELECT user_id, question, timestamp FROM logs ORDER BY id DESC LIMIT 10")
    rows = cur.fetchall()
    conn.close()
    if not rows:
        bot.send_message(message.chat.id, "Логов ещё нет.")
        return
    text = "Последние 10 запросов:\n" + "\n".join([f"{r[2]} | {r[0]}: {r[1]}" for r in rows])
    bot.send_message(message.chat.id, text)

if __name__ == "__main__":
    print("все ок, бот запущен")
    bot.polling(none_stop=True)

