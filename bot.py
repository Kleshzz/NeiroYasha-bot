import logging
import json
import os
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

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_users(users_set):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(list(users_set), f, ensure_ascii=False, indent=2)

def add_user(user_id):
    users = load_users()
    users.add(user_id)
    save_users(users)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)
    await update.message.reply_text("Привет, Я НейроПроха! Напиши мне любое сообщение и я отвечу на него в стиле ботанического сада")

async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE):
    faq_text = (
        "❓ Что это за бот?"
        "Это нейропроха - ботанически-зубрильный овощ, т.е. ИИ-ассистент, созданный для общения в формате отличников в твоем классе! Он отвечает на ваши сообщения - от простых вопросов до хамства."

        "❓ Как это работает?"
        "1. API Телеграмма принимает сообщения и отправляет ответы"
        "2. ИИ - бот использует бесплатный API Deepseek-R1 от io.net"
        "3. Бот отправляет запрос к ИИ и уже от него он доходит до вас"

        "❓ Где найти исходный код?"
        "Исходный код бота опубликован на GitHub:"
        ""

        "❓ Как связаться с автором?"
        "Telegram: @boranick"
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
        except Exception as e:
            logging.warning(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
            fail_count += 1

    await update.message.reply_text(
        f"Рассылка завершена!\n"
        f"Успешно: {success_count}\n"
        f"Неудачно: {fail_count}"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    user_text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    reply = await generate_reply(user_text)
    await update.message.reply_text(reply)

def main():
    with open("config.json", "r", encoding="utf-8") as f:
        cfg = json.load(f)

    TELEGRAM_TOKEN = cfg["TELEGRAM_TOKEN"]

    application = Application.builder().token(TELEGRAM_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("send", send))
    application.add_handler(CommandHandler("faq", faq))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling()

if __name__ == "__main__":
    main()
