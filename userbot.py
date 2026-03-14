import asyncio
import sys
import re
import os

# ФИКС: Создаем loop ДО импорта pyrogram для Python 3.12+
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters

# --- ДАННЫЕ ---
API_ID = 39875484
API_HASH = "dbde6e9d01ba04bcea2f10609054a446"
GROUP_ID = -1003704000746 
RADAR_USERNAME = "MenntionsBot" 
SECRET_KEY = "AGENT_DATA_777"

app = Client("my_account", api_id=API_ID, api_hash=API_HASH)

@app.on_message(filters.chat(GROUP_ID))
async def catch_tags(client, message):
    text = message.text or message.caption
    if not text: return
    
    tags = set(re.findall(r'#\w+', text.lower()))
    if not tags: return

    # --- УМНОЕ ОПРЕДЕЛЕНИЕ ОТПРАВИТЕЛЯ ---
    sender = "Аноним/Бот"
    
    if message.forward_from:
        sender = message.forward_from.first_name # Если аккаунт открыт
    elif message.forward_sender_name:
        sender = message.forward_sender_name     # Если аккаунт скрыт
    elif message.forward_from_chat:
        sender = message.forward_from_chat.title # Если из канала
    elif message.from_user:
        sender = message.from_user.first_name    # Обычное сообщение
    elif message.sender_chat:
        sender = message.sender_chat.title       # От имени группы/анонимного админа
    # ------------------------------------

    # --- ИСПРАВЛЕНИЕ ССЫЛКИ ---
    chat_id_str = str(message.chat.id)
    if chat_id_str.startswith("-100"):
        clean_cid = chat_id_str[4:]
    else:
        clean_cid = chat_id_str.lstrip("-")
        
    link = f"https://t.me/c/{clean_cid}/{message.id}"
    # --------------------------
    
    payload = f"{SECRET_KEY}\n{' '.join(tags)}\n{sender}\n{link}\n{text}"
    
    try:
        await client.send_message(RADAR_USERNAME, payload)
        print(f"📡 Тэг пойман и отправлен!")
    except Exception as e:
        print(f"❌ Ошибка отправки: {e}")

if __name__ == "__main__":
    if os.path.exists("my_account.session"):
        print("✅ Файл сессии найден. Старт!")
    else:
        print("❌ ФАЙЛ СЕССИИ НЕ НАЙДЕН!")
    app.run()
