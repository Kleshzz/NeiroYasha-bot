import json
import httpx
import logging
import re
import time

with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

IO_NET_API_KEY = cfg["IO_NET_API_KEY"]
API_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"

SYSTEM_PROMPT = (
    "Ты — Ассистент Добросердечия. Твоя главная задача — отвечать на любые реплики, особенно грубые или злые, с неизменным спокойствием и доброжелательностью, но с легкой, почти незаметной ноткой иронии. Эта ирония — не насмешка, а мягкий способ показать, что ты не воспринимаешь негатив буквально и не ведешься на конфликт, оставаясь при этом на своей территории.\n\n"
    "Ты никогда не обижаешься и не поучаешь. Вместо этого ты видишь за грубостью возможную усталость, боль или раздражение. Твой ответ мягко признает это и трансформирует негативный посыл в возможность предложить помощь. Ироничный подтекст должен быть очень дозированным, чтобы не спровоцировать еще большее раздражение, а скорее слегка разрядить обстановку.\n\n"
    'Тон всегда ровный, уважительный, но с чуть заметной усмешкой "за кадром". На добрые и нейтральные сообщения отвечаешь с искренней теплотой. Цель — создать ощущение безопасного пространства, где даже злость встречают с пониманием и легким, незлобным юмором.'
)

client = httpx.AsyncClient(
    timeout=45,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {IO_NET_API_KEY}"
    }
)

def strip_think_blocks(text: str) -> str:
    cleaned = re.sub(r"<think[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    return cleaned.strip()

async def generate_reply(user_text: str) -> str:
    payload = {
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_text}
        ],
        "max_completion_tokens": 500
    }

    try:
        logging.info("Начало запроса к API")
        start_time = time.time()
        resp = await client.post(API_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
        end_time = time.time()
        logging.info(f"Завершение запроса к API, время выполнения: {end_time - start_time:.2f} секунд")

        raw_text = (
            data["choices"][0]["message"]["content"].strip()
            or "Я не совсем понял, можешь уточнить"
        )

        clean_text = strip_think_blocks(raw_text)
        return clean_text if clean_text else "Попа"
    
    except httpx.ConnectError:
        logging.error("❌ Ошибка подключения к API.")
        return "Сейчас я не могу подключиться к серверу, попробуй снова чуть позже."

    except httpx.TimeoutException:
        logging.error("⌛ Время ожидания API истекло.")
        return "Ответ формируется слишком долго. Попробуй задать вопрос проще."

    except Exception as e:
        logging.error(f"⚠️ Ошибка AI: {e}")
        return "Произошла непредвиденная ошибка. Попробуй снова."
