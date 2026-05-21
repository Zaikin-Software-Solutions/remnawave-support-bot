FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Сначала только манифест зависимостей — лучшее кеширование слоёв.
COPY pyproject.toml ./

# Ставим зависимости из pyproject (без самого пакета — он копируется ниже).
RUN pip install \
    "aiogram>=3.27,<4" \
    "aiosqlite>=0.20" \
    "httpx>=0.27" \
    "python-dotenv>=1.0" \
    "pydantic>=2.7" \
    "pydantic-settings>=2.4"

COPY app ./app

# Том под SQLite. DB_PATH по умолчанию /data/bot.db (см. .env.example).
VOLUME ["/data"]

CMD ["python", "-m", "app.main"]
