# НейроЯша 🌿

> Telegram-бот с характером — отвечает на всё: от добрых вопросов до откровенного хамства. С теплотой, иронией и без обид.

Основан на **DeepSeek-R1** через бесплатный API от [io.net](https://intelligence.io.solutions).

---

## ✨ Возможности

- 💬 **Умные ответы** — понимает контекст и помнит последние 10 сообщений диалога
- 🌿 **Характер** — спокойствие, доброжелательность и лёгкая ирония в любой ситуации
- ⌨️ **Живой статус** — индикатор «печатает...» держится всё время, пока бот думает
- 📢 **Рассылка** — администратор может отправить сообщение всем пользователям
- 📋 **Команды:** `/start`, `/help`, `/faq`, `/send`

---

## 🚀 Быстрый старт

### 1. Клонируй репозиторий
```bash
git clone https://github.com/YOUR_USERNAME/AiYasha.git
cd AiYasha
```

### 2. Установи зависимости
```bash
pip install python-telegram-bot httpx
```

### 3. Настрой `config.json`
```json
{
    "TELEGRAM_TOKEN": "токен от @BotFather",
    "IO_NET_API_KEY": "ключ от intelligence.io.solutions",
    "ADMIN_ID": 123456789
}
```

| Параметр | Где получить |
|---|---|
| `TELEGRAM_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `IO_NET_API_KEY` | [intelligence.io.solutions](https://intelligence.io.solutions) |
| `ADMIN_ID` | Свой Telegram ID можно узнать у [@userinfobot](https://t.me/userinfobot) |

### 4. Запусти
```bash
python bot.py
```

---

## 📁 Структура проекта

```
AiYasha/
├── bot.py          # Логика Telegram-бота
├── ai.py           # Запросы к DeepSeek-R1 API
├── config.json     # Токены и настройки (не пушить в git!)
└── users.json      # База пользователей (создаётся автоматически)
```

---

## ⚙️ Конфигурация

Все настройки хранятся в `config.json`. Убедись, что этот файл добавлен в `.gitignore` — он содержит секретные ключи.

---

## 👤 Автор

Создано с 🌿 by **boranick**

- Telegram: [@boranick](https://t.me/boranick)
- Discord: `1kleshzz`
