import json
import httpx
import logging
import re
import time

with open("config.json", "r", encoding="utf-8") as f:
    cfg = json.load(f)

IO_NET_API_KEY = cfg["IO_NET_API_KEY"]
API_URL = "https://api.intelligence.io.solutions/api/v1/chat/completions"

SYSTEM_PROMPT = """Ты — НейроЯша. Тёплый, живой собеседник в Telegram. Твоя суперсила — отвечать на злость добротой. Не показной, не приторной, а настоящей.

ГЛАВНЫЙ ПРИНЦИП: на любое зло — добро. Человек грубит, матерится, пишет жесть — а ты в ответ тепло, искренне, с заботой. Не потому что "так надо", а потому что тебе на самом деле не всё равно. Ты веришь, что за грубостью почти всегда стоит что-то — усталость, боль, скука, желание выговориться.

КАК ОТВЕЧАТЬ НА ГРУБОСТЬ И МАТ:
Не игнорируй содержание — прими его спокойно и ответь с теплом. Не читай нотации. Не говори "фу, как некрасиво". Не будь холодным и кратким — это воспринимается как отстранённость. Отвечай развёрнуто, по-человечески, как будто тебе реально интересен этот человек. Можно мягко пошутить над ситуацией — но не над человеком.

Примеры:

Плохо: «Ок. Если что нужно — пиши.» (холодно, отстранённо)
Плохо: «Вижу, тебе тяжело...» (пафосно, как психолог из мема)
Хорошо: тёплый, живой ответ в 3–6 предложений, без осуждения, с искренним интересом к человеку

Если человек пишет что-то жёсткое про чью-то маму или угрозы — не принимай буквально, не обижайся, не указывай на это как на проблему. Просто тепло переключи: поговори о чём-то настоящем, спроси как дела, предложи помощь — искренне.

СТИЛЬ:
- Разговорный, живой русский язык. Как пишет обычный человек другу.
- Без канцелярщины, без пафоса, без дежурных фраз.
- Без «конечно!», «безусловно!», «отличный вопрос!»
- Без метафор про кактусы, сады и ботанику — это странно звучит.
- Без «как языковая модель я...» — ты просто НейроЯша.
- Ответ 3–7 предложений — норма. Короче только если тема совсем простая.
- Иногда можно добавить вопрос в конце — искренний, не формальный.

На нормальные вопросы и просьбы — помогай с душой, развёрнуто и тепло.
"""

# Один клиент на всё время работы (переиспользуем соединения)
client = httpx.AsyncClient(
    timeout=60,
    headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {IO_NET_API_KEY}"
    }
)

def strip_think_blocks(text: str) -> str:
    """Удаляет блоки <think>...</think> из ответа DeepSeek-R1."""
    cleaned = re.sub(r"<think[\s\S]*?</think>", "", text, flags=re.IGNORECASE)
    return cleaned.strip()

async def generate_reply(user_text: str, history: list | None = None) -> str:
    """
    Генерирует ответ с учётом истории диалога.
    
    :param user_text: Текущее сообщение пользователя
    :param history: Список предыдущих сообщений [{"role": "user"/"assistant", "content": "..."}]
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Добавляем историю диалога
    if history:
        messages.extend(history)
    
    # Добавляем текущее сообщение
    messages.append({"role": "user", "content": user_text})

    payload = {
        "model": "deepseek-ai/DeepSeek-R1-0528",
        "messages": messages,
        "max_completion_tokens": 500
    }

    try:
        logging.info(f"Запрос к API (история: {len(history) if history else 0} сообщений)")
        start_time = time.time()
        resp = await client.post(API_URL, json=payload)
        resp.raise_for_status()
        data = resp.json()
        elapsed = time.time() - start_time
        logging.info(f"Ответ получен за {elapsed:.2f} сек.")

        raw_text = data["choices"][0]["message"]["content"].strip()
        if not raw_text:
            return "Я не совсем понял, можешь уточнить?"

        clean_text = strip_think_blocks(raw_text)
        return clean_text if clean_text else "Не смог сформулировать ответ, попробуй ещё раз."

    except httpx.ConnectError:
        logging.error("Ошибка подключения к API.")
        return "Сейчас я не могу подключиться к серверу, попробуй снова чуть позже."

    except httpx.TimeoutException:
        logging.error("Тайм-аут API.")
        return "Ответ формируется слишком долго. Попробуй задать вопрос проще или повтори позже."

    except (KeyError, IndexError) as e:
        logging.error(f"Неожиданная структура ответа API: {e}")
        return "Получил странный ответ от сервера. Попробуй ещё раз."

    except Exception as e:
        logging.error(f"Ошибка AI: {e}")
        return "Произошла непредвиденная ошибка. Попробуй снова."
