# remnawave-support-bot

[![CI](https://github.com/Zaikin-Software-Solutions/remnawave-support-bot/actions/workflows/ci.yml/badge.svg)](https://github.com/Zaikin-Software-Solutions/remnawave-support-bot/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/Zaikin-Software-Solutions/remnawave-support-bot?display_name=tag&sort=semver&cacheSeconds=300)](https://github.com/Zaikin-Software-Solutions/remnawave-support-bot/releases)
[![Docker image](https://img.shields.io/badge/ghcr.io-remnawave--support--bot-blue?logo=docker&logoColor=white)](https://github.com/Zaikin-Software-Solutions/remnawave-support-bot/pkgs/container/remnawave-support-bot)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)

Telegram-бот поддержки для Remnawave-панели.

## Что делает

- Принимает сообщения клиентов в личке бота.
- Перед каждым форвардом шлёт владельцу **карточку** клиента: TG-логин, статус подписки, дата истечения, использованный трафик, UUID. Источник — Remnawave API.
- Форвардит само сообщение клиента владельцу.
- Клиенту автоматически отвечает: «Принято! Администратор скоро вернётся с обратной связью.» (текст настраивается).
- Владелец отвечает через **Reply** на любое из присланных ботом сообщений (на карточку или на форвард) — бот доставит ответ исходному клиенту.
- Привязывает клиента к учётке Remnawave по deep-link: `https://t.me/<bot>?start=sub_<shortUuid>` со страницы подписки.

## Стек

- Python 3.12, aiogram 3.27, aiosqlite, httpx, pydantic-settings.
- Long polling (без webhook — на низком траффике проще и устойчивее).
- Docker + docker-compose.

## Структура

```
app/
├── main.py              # точка входа, polling
├── config.py            # настройки из env
├── db.py                # aiosqlite: users + message_links
├── remnawave.py         # httpx-клиент к Remnawave Panel API
├── texts.py             # все тексты сообщений
└── handlers/
    ├── start.py         # /start + deep-link sub_<shortUuid>
    ├── client.py        # сообщения клиентов → форвард владельцу
    └── owner.py         # ответы владельца через Reply → клиенту
```

## Деплой на VPS (где уже крутится Remnawave)

### 1. Получить `BOT_TOKEN`

В Telegram написать [@BotFather](https://t.me/BotFather):

```
/newbot
<имя бота, например: Z-VPN Support>
<username бота, например: myvpn_support_bot>
```

BotFather пришлёт токен вида `123456789:AAH...` — это `BOT_TOKEN`.

Сразу же там же: `/setprivacy` → выбрать бота → **Disable**. Это нужно, чтобы бот видел все сообщения в личке (в личке это и так работает, но привычка).

### 2. Узнать свой `OWNER_TG_ID`

Написать [@userinfobot](https://t.me/userinfobot) — он пришлёт ваш числовой ID. Это `OWNER_TG_ID`.

### 3. Создать API-токен в Remnawave

Админка → **Settings → API Tokens → Create**. Скопировать токен — это `REMNAWAVE_API_TOKEN`. Базовый URL панели (тот, что в браузере для админки) — это `REMNAWAVE_BASE_URL`.

### 4. Развернуть бот

#### Вариант A — из готового образа GHCR (рекомендуется)

CI каждый push в `main` и каждый тег `vX.Y.Z` собирает multi-arch образ
(`linux/amd64` + `linux/arm64`) и публикует в
`ghcr.io/zaikin-software-solutions/remnawave-support-bot`. Никакой компиляции на сервере не нужно.

```bash
mkdir -p /opt/remnawave-support-bot && cd /opt/remnawave-support-bot

# Подтянуть compose и env-шаблон из репо.
curl -sSL https://raw.githubusercontent.com/Zaikin-Software-Solutions/remnawave-support-bot/main/docker-compose.yml -o docker-compose.yml
curl -sSL https://raw.githubusercontent.com/Zaikin-Software-Solutions/remnawave-support-bot/main/.env.example -o .env

# Заполнить BOT_TOKEN, OWNER_TG_ID, REMNAWAVE_BASE_URL, REMNAWAVE_API_TOKEN.
$EDITOR .env

# Папка под SQLite-базу. docker-compose монтирует ./data:/data.
mkdir -p data

docker compose pull
docker compose up -d
docker compose logs -f support-bot
```

Чтобы зафиксировать версию — замените `:latest` в `docker-compose.yml` на
`:1.0.0` (или `:1` / `:1.0` — floating major / minor). Обновление:
`docker compose pull && docker compose up -d`.

#### Вариант B — сборка из исходников (для локальной разработки)

```bash
git clone https://github.com/Zaikin-Software-Solutions/remnawave-support-bot.git
cd remnawave-support-bot
cp .env.example .env
$EDITOR .env
mkdir -p data
docker compose -f docker-compose.yml -f docker-compose.build.yml up -d --build
docker compose logs -f support-bot
```

В логах должно появиться:
```
[INFO] bot: Starting bot, owner_tg_id=…, panel=…
```

### 5. Проверить работу

- Открыть бота в Telegram, написать `/start` — владельцу должен прийти баннер «Бот поддержки запущен».
- С другого аккаунта написать боту любое сообщение — владелец увидит карточку + форвард.
- Сделать Reply на форвард — клиент получит ответ.

### 6. Связать с subscription-страницей

В админке Remnawave **Subscription Settings → Sub Page Configs** (или эквивалент в вашей версии) добавить в правый верхний угол ссылки:

- **Поддержка (TG):** `https://t.me/<bot_username>?start=sub_{{shortUuid}}` — `{{shortUuid}}` подставляется панелью автоматически (имя плейсхолдера зависит от темы шаблона).
- **Анонсы (TG):** `https://t.me/<channel_username>` (опционально)
- **Резерв (VK / другой мессенджер):** на случай блокировки Telegram (опционально)

## Help-page

`help-page/index.html` — статичная страница «Поддержка», на которую можно ссылаться из subscription-страницы Remnawave (кнопка «Поддержка»). Это **шаблон**: внутри плейсхолдеры `your_brand`, `your_support_bot`, `your_channel`, `your_vk_username` — замените на свои перед заливкой страницы на хостинг. Сам бот её не отдаёт; разместите как обычный static-файл (nginx, Cloudflare Pages, GitHub Pages и т.п.).

## Что хранится в БД

- `users(tg_user_id, tg_username, remnawave_uuid, short_uuid, …)` — кто из TG какой подписке принадлежит.
- `message_links(owner_msg_id, client_tg_id, client_msg_id, …)` — какое сообщение у владельца соответствует какому клиенту. Используется для Reply-механики.

Файл БД лежит в `./data/bot.db` (том `data/`). Бэкап = скопировать файл.

## Локальный запуск (без docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .
cp .env.example .env  # отредактировать
DB_PATH=./data/bot.db python -m app.main
```

## Управление

```bash
docker compose logs -f support-bot     # логи
docker compose restart support-bot     # рестарт
docker compose up -d --build           # пересборка после изменений
docker compose down                    # остановка
```

## Безопасность

- `.env` с реальными токенами **никогда не коммитить** — `.gitignore` это уже учитывает.
- API-токен Remnawave даёт **полный доступ** к панели. Храните только на сервере.
- `OWNER_TG_ID` — единственный, кто может отвечать клиентам через бот. Кто-то ещё в личку бота напишет — бот будет считать его клиентом.
</content>
