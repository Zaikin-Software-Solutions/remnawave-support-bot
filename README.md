# remnawave-support-bot

Telegram-бот поддержки для Remnawave-панели.

Что делает:
- Принимает сообщения клиентов в личке.
- Форвардит каждое сообщение владельцу (`OWNER_TG_ID`) с подписью: username, статус подписки в Remnawave, дата истечения.
- Клиенту автоматически отвечает: «Администратор скоро вернётся с обратной связью».
- Владелец отвечает через **Reply** на форварднутое сообщение — бот доставит ответ исходному клиенту.
- Привязывает клиента к учётке Remnawave по deep-link `?start=sub_<shortUuid>` со страницы подписки.

## Стек

- Python 3.12, aiogram 3.27, aiosqlite, httpx.
- Long polling (без webhook — проще, на малом траффике без разницы).
- Docker + docker-compose.

## Быстрый старт

1. Скопировать `.env.example` → `.env` и заполнить:
   - `BOT_TOKEN` — у [@BotFather](https://t.me/BotFather)
   - `OWNER_TG_ID` — узнать у [@userinfobot](https://t.me/userinfobot)
   - `REMNAWAVE_BASE_URL` и `REMNAWAVE_API_TOKEN` — из панели Remnawave
2. `docker compose up -d`
3. На subscription-странице (Sub Page Config в Remnawave) добавить ссылку:
   `https://t.me/<bot_username>?start=sub_<shortUuid>`

## Структура

```
app/
├── main.py              # точка входа, запуск polling
├── config.py            # настройки из env
├── db.py                # aiosqlite слой
├── remnawave.py         # httpx-клиент к API панели
├── handlers/
│   ├── start.py         # /start + deep-link
│   ├── client.py        # сообщения от клиентов
│   └── owner.py         # ответы владельца (через reply)
└── texts.py             # тексты сообщений
```

## Локальный запуск (без docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
python -m app.main
```
