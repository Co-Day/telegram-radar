import telebot
import sqlite3
import html
import re
import threading
import time

# Вставь НОВЫЙ токен от BotFather!
TOKEN = '8625343920:AAGGh4qDSb5FnxP6l5bKdG9XmoDloPx8tGc'

# Твои админы
ADMIN_IDS = [8487270986, 6662943592, 7512605688]

bot = telebot.TeleBot(TOKEN, parse_mode='HTML')

# --- НАСТРОЙКА БАЗЫ ДАННЫХ ---
db = sqlite3.connect('tags.db', check_same_thread=False)
sql = db.cursor()

# 1. Таблица тэгов
sql.execute("CREATE TABLE IF NOT EXISTS tags (tag TEXT PRIMARY KEY, username TEXT, password TEXT, user_id INTEGER)")
try:
    sql.execute("ALTER TABLE tags ADD COLUMN notifications_enabled INTEGER DEFAULT 1")
except sqlite3.OperationalError:
    pass

# 2. Таблица-очередь (Сюда Юзербот будет скидывать сообщения)
sql.execute("CREATE TABLE IF NOT EXISTS queue (id INTEGER PRIMARY KEY AUTOINCREMENT, text TEXT, chat_username TEXT, chat_id TEXT, message_id INTEGER, sender_name TEXT)")
db.commit()


# --- СТАРТ ---
@bot.message_handler(commands=['start'])
def start(message):
    if message.chat.type != 'private':
        return

    text = (
        "👋 <b>Добро пожаловать!</b> Я бот для удобства работы с пз.\n\n"
        "Если администратор проекта выдал тебе персональный тэг, жми /login для авторизации.\n"
        "Я буду моментально оповещать тебя, если кто-то позовет тебя в чате! 🚀\n\n"
        "<i>Включать и выключать уведомления можно командой /notify</i>"
    )
    bot.send_message(message.chat.id, text)

# --- АДМИНСКАЯ ЧАСТЬ ---
@bot.message_handler(commands=['addtag'])
def add_tag(message):
    if message.chat.type != 'private' or message.from_user.id not in ADMIN_IDS:
        return

    try:
        _, tag, username, password = message.text.split()
        tag = tag.lower()

        sql.execute("INSERT OR REPLACE INTO tags (tag, username, password, user_id, notifications_enabled) VALUES (?, ?, ?, NULL, 1)", (tag, username, password))
        db.commit()

        text = (
            "✅ <b>Тэг успешно зарегистрирован!</b>\n\n"
            f"📌 <b>Тэг:</b> {tag}\n"
            f"👤 <b>Кому:</b> {username}\n"
            f"🔑 <b>Пароль:</b> <code>{password}</code>\n\n"
            "💬 <i>Передай эти данные пользователю и скажи ему написать мне команду</i> /login"
        )
        bot.send_message(message.chat.id, text)
    except ValueError:
        bot.send_message(message.chat.id, "❌ <b>Ошибка формата.</b>\nПиши так: <code>/addtag #тэг @ник пароль</code>")

@bot.message_handler(commands=['deltag'])
def del_tag(message):
    if message.chat.type != 'private' or message.from_user.id not in ADMIN_IDS:
        return

    try:
        tag = message.text.split()[1].lower()
        sql.execute("DELETE FROM tags WHERE tag=?", (tag,))
        db.commit()
        bot.send_message(message.chat.id, f"🗑 <b>Тэг {tag} успешно удален из базы.</b>")
    except IndexError:
        bot.send_message(message.chat.id, "❌ <b>Уточни тэг.</b>\nПример: <code>/deltag #тэг</code>")

@bot.message_handler(commands=['alltags'])
def show_all_tags(message):
    if message.chat.type != 'private' or message.from_user.id not in ADMIN_IDS:
        return

    sql.execute("SELECT tag, username, password, user_id, notifications_enabled FROM tags")
    rows = sql.fetchall()

    if not rows:
        bot.send_message(message.chat.id, "📭 <b>База тэгов пуста.</b>")
        return

    text = "📋 <b>Список всех зарегистрированных тэгов:</b>\n\n"
    for row in rows:
        if row[3]:
            status = "✅ В сети (🔔 Вкл)" if row[4] == 1 else "💤 В сети (🔕 Выкл)"
        else:
            status = "⏳ Ожидает входа"

        text += (
            f"🔹 <b>Тэг:</b> {row[0]}\n"
            f"👤 <b>Ник:</b> {row[1]}\n"
            f"🔑 <b>Пароль:</b> <code>{row[2]}</code>\n"
            f"📊 <b>Статус:</b> {status}\n"
            f"────────────────────\n"
        )

    bot.send_message(message.chat.id, text)

# --- ПОЛЬЗОВАТЕЛЬСКАЯ ЧАСТЬ ---
@bot.message_handler(commands=['login'])
def login_start(message):
    if message.chat.type != 'private':
        return

    text = (
        "🔐 <b>Авторизация тэга</b>\n\n"
        "Отправь мне свой тэг и пароль через пробел.\n"
        "<i>Например:</i> <code>#animator 12345</code>"
    )
    msg = bot.send_message(message.chat.id, text)
    bot.register_next_step_handler(msg, process_login)

def process_login(message):
    if message.chat.type != 'private':
        bot.clear_step_handler_by_chat_id(message.chat.id)
        return

    try:
        tag, password = message.text.split()
        tag = tag.lower()

        sql.execute("SELECT password FROM tags WHERE tag=?", (tag,))
        result = sql.fetchone()

        if result and result[0] == password:
            sql.execute("UPDATE tags SET user_id=? WHERE tag=?", (message.from_user.id, tag))
            db.commit()
            bot.send_message(message.chat.id, "🎉 <b>Успешный вход!</b>\nТеперь система активна. Жди уведомлений!\n\n<i>Включать и выключать уведомления можно командой /notify</i>")
        else:
            bot.send_message(message.chat.id, "❌ <b>Неверный тэг или пароль.</b>\nНачни заново через /login")
    except ValueError:
        bot.send_message(message.chat.id, "❌ <b>Ошибка ввода.</b>\nНужно прислать тэг и пароль через пробел.")

# --- УПРАВЛЕНИЕ УВЕДОМЛЕНИЯМИ ---
@bot.message_handler(commands=['notify'])
def toggle_notifications(message):
    if message.chat.type != 'private':
        return

    sql.execute("SELECT tag, notifications_enabled FROM tags WHERE user_id=?", (message.from_user.id,))
    user_data = sql.fetchone()

    if not user_data:
        bot.send_message(message.chat.id, "❌ <b>Вы еще не авторизованы.</b>\nСначала используйте /login")
        return

    tag, current_state = user_data

    # Меняем состояние: 1 -> 0, 0 -> 1
    new_state = 0 if current_state == 1 else 1

    sql.execute("UPDATE tags SET notifications_enabled=? WHERE user_id=?", (new_state, message.from_user.id))
    db.commit()

    if new_state == 0:
        bot.send_message(message.chat.id, f"🔕 <b>Уведомления отключены!</b>\nЯ больше не буду беспокоить вас по тэгу {tag}.\n\n<i>Чтобы включить обратно, снова нажмите /notify</i>")
    else:
        bot.send_message(message.chat.id, f"🔔 <b>Уведомления включены!</b>\nЯ снова слежу за тэгом {tag} в чатах.\n\n<i>Чтобы выключить, снова нажмите /notify</i>")


# ==========================================
# --- ЧТЕЦ "ПОЧТОВОГО ЯЩИКА" (ОТ ЮЗЕРБОТА) ---
# ==========================================
def check_mailbox():
    while True:
        try:
            time.sleep(1) # Проверяем каждую секунду
            local_db = sqlite3.connect('tags.db', check_same_thread=False)
            local_sql = local_db.cursor()
            
            local_sql.execute("SELECT * FROM queue")
            messages = local_sql.fetchall()
            
            for msg in messages:
                msg_id, text, chat_username, chat_id, message_id, sender_name = msg
                
                if not text:
                    local_sql.execute("DELETE FROM queue WHERE id=?", (msg_id,))
                    local_db.commit()
                    continue

                tags_in_message = set(re.findall(r'#\w+', text.lower()))
                
                for tag in tags_in_message:
                    local_sql.execute("SELECT user_id, notifications_enabled FROM tags WHERE tag=?", (tag,))
                    user = local_sql.fetchone()
                    
                    if user and user[0] and user[1] == 1: 
                        if chat_username:
                            link = f"https://t.me/{chat_username}/{message_id}"
                        else:
                            chat_id_clean = str(chat_id).replace("-100", "")
                            link = f"https://t.me/c/{chat_id_clean}/{message_id}"
                            
                        safe_text = html.escape(text)
                        sender_safe = html.escape(sender_name)
                        
                        text_to_send = (
                            "🔔 <b>Уведомление! (через Шпиона)</b>\n\n"
                            f"👤 <b>От:</b> {sender_safe}\n"
                            f"💬 <i>«{safe_text}»</i>\n\n"
                            f"👉 <a href='{link}'>Перейти к сообщению</a>"
                        )
                        
                        try:
                            bot.send_message(user[0], text_to_send, disable_web_page_preview=True)
                        except Exception as e:
                            print(f"Ошибка пересылки из очереди: {e}")
                
                local_sql.execute("DELETE FROM queue WHERE id=?", (msg_id,))
                local_db.commit()
                
            local_db.close()
        except Exception as e:
            print(f"Ошибка в фоновом потоке: {e}")

# ==========================================
# --- МОНИТОРИНГ ГРУППЫ (ОБЫЧНЫЕ ЛЮДИ) ---
# ==========================================
@bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'], content_types=['text', 'photo', 'video', 'document'])
def check_mentions(message):
    text = message.text or message.caption
    if not text:
        return

    tags_in_message = set(re.findall(r'#\w+', text.lower()))
    
    for tag in tags_in_message:
        sql.execute("SELECT user_id, notifications_enabled FROM tags WHERE tag=?", (tag,))
        user = sql.fetchone()

        if user and user[0] and user[1] == 1:
            if message.chat.username:
                link = f"https://t.me/{message.chat.username}/{message.message_id}"
            else:
                chat_id_str = str(message.chat.id).replace("-100", "")
                link = f"https://t.me/c/{chat_id_str}/{message.message_id}"

            safe_text = html.escape(text)
            sender_name = html.escape(message.from_user.first_name)

            text_to_send = (
                "🔔 <b>Вас упомянули в чате!</b>\n\n"
                f"👤 <b>От кого:</b> {sender_name}\n"
                f"💬 <i>«{safe_text}»</i>\n\n"
                f"👉 <a href='{link}'>Перейти к сообщению</a>"
            )

            try:
                bot.send_message(user[0], text_to_send, parse_mode="HTML", disable_web_page_preview=True)
            except Exception as e:
                print(f"Ошибка отправки сообщения: {e}")

# Запуск всего механизма
print("Запускаем проверку почтового ящика...")
threading.Thread(target=check_mailbox, daemon=True).start()

print("Бот-Радар запущен! Ожидаю сообщений...")
bot.infinity_polling(timeout=10, long_polling_timeout=5)