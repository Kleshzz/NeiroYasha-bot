import logging
import json
import os
import asyncio
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from ai import generate_reply

USERS_FILE = "users.json"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# --- Кэш пользователей в памяти (не читаем файл при каждом сообщении) ---
_users_cache: set | None = None

def load_users() -> set:
    global _users_cache
    if _users_cache is None:
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, "r", encoding="utf-8") as f:
                _users_cache = set(json.load(f))
        else:
            _users_cache = set()
    return _users_cache

def save_users(users_set: set):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(users_set), f, ensure_ascii=False, indent=2)

def add_user(user_id: int):
    users = load_users()
    if user_id not in users:
        users.add(user_id)
        save_users(users)  # Пишем только если юзер новый

# --- История диалога (хранится в context.user_data) ---
MAX_HISTORY = 10  # последних пар сообщений

def get_history(context: ContextTypes.DEFAULT_TYPE) -> list:
    return context.user_data.setdefault("history", [])

def append_history(context: ContextTypes.DEFAULT_TYPE, role: str, content: str):
    history = get_history(context)
    history.append({"role": role, "content": content})
    # Ограничиваем историю: MAX_HISTORY пар = MAX_HISTORY*2 сообщений
    if len(history) > MAX_HISTORY * 2:
        context.user_data["history"] = history[-(MAX_HISTORY * 2):]


# --- Helpers ---
async def keep_typing(bot, chat_id: int, stop_event: asyncio.Event):
    """Периодически обновляет статус 'печатает...' пока бот думает."""
    while not stop_event.is_set():
        await bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        try:
            await asyncio.wait_for(asyncio.shield(stop_event.wait()), timeout=4.5)
        except asyncio.TimeoutError:
            pass


# --- Команды ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    context.user_data.clear()  # Сброс истории при /start
    await update.message.reply_text(
        "Привет! Я НейроЯша 🌿\n"
        "Напиши мне что угодно — отвечу с теплотой и лёгкой иронией.\n\n"
        "Команды:\n"
        "/start — начать заново (сброс истории)\n"
        "/faq — вопросы и ответы\n"
        "/help — справка"
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📖 *Как пользоваться ботом*\n\n"
        "Просто пиши любое сообщение — я отвечу.\n"
        "Я помню контекст нашего разговора (последние 10 сообщений).\n\n"
        "Чтобы начать новый диалог — /start\n"
        "Вопросы и ответы — /faq",
        parse_mode="Markdown"
    )

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faq_text = (
        "❓ *Что это за бот?*\n"
        "НейроЯша — тёплый ИИ-собеседник: "
        "отвечает спокойно, с теплотой и лёгкой иронией.\n\n"

        "❓ *Как это работает?*\n"
        "1. Telegram API принимает сообщения\n"
        "2. Бот использует бесплатный API DeepSeek-R1 от io.net\n"
        "3. Ответ возвращается тебе\n\n"

        "❓ *Где исходный код?*\n"
        "На GitHub — ищи AiYasha\n\n"

        "❓ *Как связаться с автором?*\n"
        "Telegram: @boranick\n"
        "Discord: 1kleshzz"
    )
    await update.message.reply_text(faq_text, parse_mode="Markdown")

async def send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)
    ADMIN_ID = cfg.get("ADMIN_ID")

    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("Использование: /send <текст рассылки>")
        return

    message_text = " ".join(context.args)
    users = load_users()
    success_count = 0
    fail_count = 0

    await update.message.reply_text(f"Начинаю рассылку для {len(users)} пользователей...")

    for user_id in users:
        try:
            await context.bot.send_message(chat_id=user_id, text=message_text)
            success_count += 1
            await asyncio.sleep(0.05)  # Защита от flood limit
        except Exception as e:
            logging.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            fail_count += 1

    await update.message.reply_text(
        f"Рассылка завершена!\n"
        f"✅ Успешно: {success_count}\n"
        f"❌ Неудачно: {fail_count}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    user_text = update.message.text

    # Запускаем бесконечный "печатает..." пока ждём ответа
    stop_event = asyncio.Event()
    typing_task = asyncio.create_task(
        keep_typing(context.bot, update.effective_chat.id, stop_event)
    )

    try:
        history = get_history(context)
        reply = await generate_reply(user_text, history)
    finally:
        stop_event.set()
        typing_task.cancel()

    append_history(context, "user", user_text)
    append_history(context, "assistant", reply)

    await update.message.reply_text(reply)


def main():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    TELEGRAM_TOKEN = cfg["TELEGRAM_TOKEN"]

    # Прогреваем кэш пользователей при старте
    load_users()
    logging.info(f"Загружено {len(_users_cache)} пользователей")

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("send", send))
    application.add_handler(CommandHandler("faq", faq))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
