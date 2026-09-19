# VibeCoder Assistant

Telegram-бот-консультант по портфолио VibeCoder. Описание продукта и правила разработки — в `CLAUDE.md`.

## Запуск

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # заполнить BOT_TOKEN и остальное
python bot.py
```

## База данных

Заявки на бриф хранятся в SQLite: `data/vibecoder_bot.db` (создаётся
автоматически при первом запуске). Посмотреть содержимое можно, например,
через [DB Browser for SQLite](https://sqlitebrowser.org/) или командой:

```bash
sqlite3 data/vibecoder_bot.db "SELECT * FROM leads;"
```

Лендинг сейчас статический (HTML/CSS/JS без бэкенда), поэтому это
отдельная база бота, а не общая с лендингом, как изначально предполагал
паспорт. Если у лендинга появится сервер — схему легко перенести.
