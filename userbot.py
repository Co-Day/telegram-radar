import asyncio
asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters
import sqlite3
import re

API_ID = 39875484
API_HASH = "dbde6e9d01ba04bcea2f10609054a446"
GROUP_ID = -5214640155

app = Client("my_account", api_id=API_ID, api_hash=API_HASH)

@app.on_message(filters.chat(GROUP_ID))
async def catch_tags(client, message):
    # Берем текст из сообщения ИЛИ из пересланного сообщения (важно!)
    text = message.text or message.caption
    if not text and message.forward_from_chat or message.forward_from:
        # Если это пересланное сообщение без своего текста, пробуем взять текст оригинала
        text = message.text or message.caption

    if not text:
        return

    tags_in_message = set(re.findall(r'#\w+', text.lower()))
    if not tags_in_message:
        return

    # Определяем отправителя
    sender = "Аноним/Бот"
    if message.from_user:
        sender = message.from_user.first_name
    elif message.sender_chat:
        sender = message.sender_chat.title

    try:
        db = sqlite3.connect('tags.db', check_same_thread=False)
        sql = db.cursor()
        
        # Чистим ID группы для ссылки (убираем -100)
        clean_cid = str(message.chat.id).replace("-100", "")
        
        sql.execute(
            "INSERT INTO queue (text, chat_username, chat_id, message_id, sender_name) VALUES (?, ?, ?, ?, ?)",
            (text, message.chat.username, clean_cid, message.id, sender)
        )
        db.commit()
        db.close()
        print(f"✅ Поймал тэг в сообщении (возможно пересланном)!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    app.run()
