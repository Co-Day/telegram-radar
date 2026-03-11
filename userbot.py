from pyrogram import Client, filters
import sqlite3
import re
import asyncio

# Данные из my.telegram.org
API_ID = 39875484
API_HASH = "dbde6e9d01ba04bcea2f10609054a446"

# ID твоей группы (ПЗ)
GROUP_ID = -5214640155

# --- НАСТРОЙКА КЛИЕНТА ЧЕРЕЗ MTPROTO PROXY ---
# Данные взяты с твоего скриншота (Proxy MTProto)
app = Client(
    "my_account", 
    api_id=API_ID, 
    api_hash=API_HASH,
    proxy=dict(
        hostname="194.120.230.106",
        port=433,  # Если не пойдет, замени на 443
        secret="3XnnAQIAAQAH8AMDhuJM0t0"
    )
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
        print(f"👀 Агент поймал тэг(и) {tags_in_message} и передал Радару!")
    except Exception as e:
        print(f"❌ Ошибка базы данных у Агента: {e}")

# Запуск программы
if __name__ == "__main__":
    print("🚀 Агент запущен через MTProto Proxy!")
    print("📡 Мониторинг группы ПЗ активирован...")
    app.run()