import asyncio
import sys

# ФИКС: Создаем loop ДО импорта pyrogram для Python 3.12+
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters
import re
import os

# --- ДАННЫЕ ---
API_ID = 39875484
API_HASH = "dbde6e9d01ba04bcea2f10609054a446"
GROUP_ID = -5214640155 
RADAR_USERNAME = "MenntionsBot" # Например: MyBestRadarBot
SECRET_KEY = "AGENT_DATA_777"

app = Client("my_account", api_id=API_ID, api_hash=API_HASH)

@app.on_message(filters.chat(GROUP_ID))
async def catch_tags(client, message):
    text = message.text or message.caption
    if not text: return
    
    tags = set(re.findall(r'#\w+', text.lower()))
    if not tags: return

    sender = message.from_user.first_name if message.from_user else "Аноним"
    clean_cid = str(message.chat.id).replace("-100", "")
    link = f"https://t.me/c/{clean_cid}/{message.id}"
    
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

