import asyncio
# Фикс для работы на новых версиях Python (Render)
asyncio.set_event_loop(asyncio.new_event_loop())

from pyrogram import Client, filters
import re

# --- ТВОИ ДАННЫЕ ---
API_ID = 39875484
API_HASH = "dbde6e9d01ba04bcea2f10609054a446"

# ID группы ПЗ, которую слушаем
GROUP_ID = -1002446777647 # Убедись, что ID именно такой (с -100)

# Юзернейм твоего бота-радара (БЕЗ @)
RADAR_USERNAME = "ВСТАВЬ_СЮДА_ЮЗЕРНЕЙМ_БОТА" 

# Секретный ключ (должен быть таким же, как в коде Радара!)
SECRET_KEY = "AGENT_DATA_777"

app = Client("my_account", api_id=API_ID, api_hash=API_HASH)

@app.on_message(filters.chat(GROUP_ID))
async def catch_tags(client, message):
    # Берем текст или описание медиафайла
    text = message.text or message.caption
    if not text:
        return

    # Ищем тэги
    tags = set(re.findall(r'#\w+', text.lower()))
    if not tags:
        return

    # Определяем имя отправителя
    if message.from_user:
        sender = message.from_user.first_name
    elif message.sender_chat:
        sender = message.sender_chat.title
    else:
        sender = "Аноним"

    # Создаем ссылку на сообщение (для закрытых групп)
    clean_cid = str(message.chat.id).replace("-100", "")
    link = f"https://t.me/c/{clean_cid}/{message.id}"
    
    # Формируем пакет данных для Радара
    # Формат: КЛЮЧ \n ТЭГИ \n ИМЯ \n ССЫЛКА \n ТЕКСТ
    payload = f"{SECRET_KEY}\n{' '.join(tags)}\n{sender}\n{link}\n{text}"
    
    try:
        # Отправляем Радару в личку
        await client.send_message(RADAR_USERNAME, payload)
        print(f"✅ Поймал тэги {tags}. Отправил Радару.")
    except Exception as e:
        print(f"❌ Ошибка отправки Радару: {e}")

if __name__ == "__main__":
    print("🚀 Агент (Юзербот) запущен!")
    print(f"📡 Мониторинг группы {GROUP_ID} активен...")
    app.run()
