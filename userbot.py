import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters
import sqlite3
import re

# Данные из my.telegram.org
API_ID = 39875484
API_HASH = "dbde6e9d01ba04bcea2f10609054a446"

# ID твоей группы (ПЗ)
GROUP_ID = -5214640155

# --- НАСТРОЙКА КЛИЕНТА ---
# Без прокси, так как на Render открытый интернет
app = Client(
    "my_account", 
    api_id=API_ID, 
    api_hash=API_HASH
)

# Асинхронный обработчик сообщений
@app.on_message(filters.chat(GROUP_ID))
async def catch_tags(client, message):
    # Достаем текст или подпись к фото/видео
    text = message.text or message.caption
    if not text:
        return

    # Ищем все тэги (например, #tag1 #work)
    tags_in_message = set(re.findall(r'#\w+', text.lower()))
    
    if not tags_in_message:
        return

    # Определяем, кто отправил сообщение
    if message.from_user:
        sender = message.from_user.first_name or "Без имени"
    elif message.sender_chat:
        sender = message.sender_chat.title
    else:
        sender = "Аноним/Бот"

    try:
        # Подключаемся к общей базе данных tags.db
        db = sqlite3.connect('tags.db', check_same_thread=False)
        sql = db.cursor()
        
        # Записываем данные в очередь для основного бота (Радара)
        sql.execute(
            "INSERT INTO queue (text, chat_username, chat_id, message_id, sender_name) VALUES (?, ?, ?, ?, ?)",
            (
                text, 
                message.chat.username, 
                str(message.chat.id), 
                message.id, 
                sender
            )
        )
        db.commit()
        db.close()
        print(f"👀 Агент поймал тэг(и) {tags_in_message} и передал Радару через базу!")
    except Exception as e:
        print(f"❌ Ошибка базы данных у Агента: {e}")

# Запуск программы
if __name__ == "__main__":
    print("🚀 Агент запущен на Render!")
    print("📡 Мониторинг группы ПЗ активирован...")
    app.run()

