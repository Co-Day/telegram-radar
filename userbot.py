import asyncio
import os
import re
from pyrogram import Client, filters

# Фикс для работы на Render
asyncio.set_event_loop(asyncio.new_event_loop())

# --- ПРОВЕРКА ФАЙЛА СЕССИИ ---
if os.path.exists("my_account.session"):
    print("✅ Файл сессии найден! Пытаюсь войти...")
else:
    print("❌ ОШИБКА: Файл my_account.session не найден в корне проекта!")

# --- ТВОИ ДАННЫЕ ---
API_ID = 39875484
API_HASH = "dbde6e9d01ba04bcea2f10609054a446"
GROUP_ID = -1002446777647 
RADAR_USERNAME = "ВСТАВЬ_НИК_БОТА_БЕЗ_@"  # <-- ПРОВЕРЬ ЭТО!
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
        print(f"📡 Тэг пойман и отправлен Радару!")
    except Exception as e:
        print(f"❌ Ошибка пересылки: {e}")

if __name__ == "__main__":
    print("🚀 Агент (Юзербот) успешно стартовал!")
    app.run()
